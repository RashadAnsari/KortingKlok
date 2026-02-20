import html as html_mod
import json
import re
import time
from decimal import Decimal
from urllib.parse import unquote, urlparse

import requests

from products.scrapers.base import BaseSupermarketScraper
from products.scrapers.dtos import ScrapedCategory, ScrapedProduct
from products.scrapers.registry import register_scraper

BASE_URL = "https://www.lidl.nl"
ASSORTMENT_PATH = "/c/assortiment-producten/s10008015"
DEALS_PATH = "/c/aanbiedingen/a10008785"

# Polite delay between consecutive HTTP requests.
REQUEST_DELAY = 0.5

# Safety ceiling: never paginate beyond this offset for a single page.
MAX_OFFSET = 48 * 100  # 4800 products per category

# Pre-compiled regex patterns (avoids re-compilation on every loop iteration)
_RE_CARD_LIST = re.compile(r'ATheContentPageCardList__Item--linked"\s+href="([^"]+)"\s+data-unified-click="([^"]+)"')
_RE_NAV_LINK = re.compile(r'href="([^"]+)"[^>]*data-ga-label="([^"]+)"')
_RE_NAV_H = re.compile(r"/h/[^/]+/h\d+")
_RE_ANCHOR_CAT = re.compile(r'href="(/[hc]/[^"?#]+/[has]\d+[^"]*)"[^>]*>([^<]{1,100})<')
_RE_NUXT_SCRIPT = re.compile(r'<script[^>]*id=["\']__nuxt_data__["\'][^>]*>(.*?)</script>', re.DOTALL | re.IGNORECASE)
_RE_NUXT_TRIPLET = re.compile(r'"(\d{6,})","([^"]{2,80})","(/[hc]/[^/"]+/[has]\d+)"')
_RE_GRID_DATA = re.compile(r'data-grid-data="([^"]*?)"')
_RE_PATH_ID = re.compile(r"/([ash]\d+)(?:[/?#]|$)")
_RE_BRACKET_SUFFIX = re.compile(r"\s*\(.*?\)\s*$")

# Top-level section/nav pages that are not product-listing pages themselves.
_SECTION_IDS = frozenset(["s10008015", "s10008009"])

# Known non-product /c/ pages (legal, info, brand-index, service pages).
# We skip these during category discovery to avoid polluting the DB.
_NONCAT_IDS = frozenset(
    [
        "s10004350",
        "s10004348",
        "s10004349",
        "s10004059",
        "s10008149",
        "s10003480",
        "s10011768",
        "s10048217",
        "s10023965",
        "s10004364",
        "s10008391",
        "s10008463",
        "s10008464",
        "s10008100",
        "s10008099",
        "s10077968",
    ]
)

# Merge for a single "skip" set used in category extraction.
_SKIP_IDS = _SECTION_IDS | _NONCAT_IDS


@register_scraper
class LidlScraper(BaseSupermarketScraper):
    supermarket_slug = "lidl"

    def __init__(self):
        super().__init__()
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/131.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "nl-NL,nl;q=0.9,en;q=0.8",
            }
        )
        # external_id → clean URL for every discovered category page.
        self._category_urls: dict[str, str] = {}
        # name → external_id mapping for matching deal products to categories.
        self._category_name_to_id: dict[str, str] = {}
        # url → HTML cache populated during category BFS.
        # Avoids re-fetching the same offset=0 page during product scraping.
        self._page_cache: dict[str, str] = {}

    def scrape_categories(self) -> list[ScrapedCategory]:
        categories: list[ScrapedCategory] = []
        seen_ids: set[str] = set()

        # Step 1: extract top-level categories from the main assortment page.
        # This catches both:
        #   • the 71 /h/ hierarchy categories in the site-wide header nav
        #   • the food/assortment /c/ categories in the page body cards
        assortment_html = self._fetch_page(ASSORTMENT_PATH)

        # Primary: card-list layout (body cards, typically food categories).
        card_cats = self._extract_card_list_categories(assortment_html)
        for cat in card_cats:
            if cat.external_id not in seen_ids:
                seen_ids.add(cat.external_id)
                categories.append(cat)

        # Secondary: navigation link layout — covers the 71 /h/ top-level cats.
        nav_cats = self._extract_nav_categories(assortment_html)
        for cat in nav_cats:
            if cat.external_id not in seen_ids:
                seen_ids.add(cat.external_id)
                categories.append(cat)

        # Step 2: BFS — visit each category page and discover sub-categories.
        # New sub-categories are added to the queue as they are found.
        queue: list[ScrapedCategory] = list(categories)
        while queue:
            parent_cat = queue.pop(0)
            cat_url = self._category_urls.get(parent_cat.external_id)
            if not cat_url:
                continue

            time.sleep(REQUEST_DELAY)
            try:
                page_html = self._fetch_page(cat_url)
            except Exception as exc:
                self.logger.warning(
                    "Error fetching category %s (%s): %s",
                    parent_cat.external_id,
                    cat_url,
                    exc,
                )
                continue

            # a) Anchor-tag based discovery.
            anchor_subs = self._extract_category_links(
                page_html,
                parent_id=parent_cat.external_id,
                seen_ids=seen_ids,
            )
            # b) Nuxt SSR data discovery (finds deeply nested sub-categories).
            nuxt_subs = self._extract_nuxt_categories(
                page_html,
                parent_id=parent_cat.external_id,
                seen_ids=seen_ids,
            )

            for sub_cat in anchor_subs + nuxt_subs:
                seen_ids.add(sub_cat.external_id)
                categories.append(sub_cat)
                queue.append(sub_cat)

        self._category_name_to_id = {c.name: c.external_id for c in categories}
        return categories

    def scrape_products(self) -> list[ScrapedProduct]:
        seen: dict[str, ScrapedProduct] = {}
        last_logged = 0

        # Pass 1: paginate through every known category page sequentially.
        # Sleep before each category (not just between pages within a category)
        # to avoid CPU/network bursts when the first page is already cached.
        for cat_id, cat_url in self._category_urls.items():
            try:
                self._scrape_category_pages(cat_id, cat_url, seen)
            except Exception as exc:
                self.logger.warning("Error scraping products for category %s: %s", cat_id, exc)
            if len(seen) - last_logged >= 1000:
                self.logger.info("Scraped %d products so far", len(seen))
                last_logged = len(seen)
            time.sleep(REQUEST_DELAY)

        # Pass 2: deals page — products have live pricing, overwrite assortment.
        self._scrape_deals_pages(seen)
        return list(seen.values())

    def _extract_card_list_categories(self, page_html: str) -> list[ScrapedCategory]:
        categories: list[ScrapedCategory] = []
        for href, click_data_encoded in _RE_CARD_LIST.findall(page_html):
            try:
                click_data = json.loads(unquote(click_data_encoded))
            except (json.JSONDecodeError, ValueError):
                continue

            name = click_data.get("linkName")
            if not name:
                continue

            external_id = self._extract_path_id(href)
            if not external_id or external_id in _SKIP_IDS:
                continue

            self._register_category_url(external_id, href)
            categories.append(ScrapedCategory(external_id=external_id, name=html_mod.unescape(name)))
        return categories

    def _extract_nav_categories(self, page_html: str) -> list[ScrapedCategory]:
        categories: list[ScrapedCategory] = []
        seen_ids: set[str] = set()

        for href, label in _RE_NAV_LINK.findall(page_html):
            # Accept /h/ hierarchy pages and /c/ assortment pages.
            is_h = bool(_RE_NAV_H.search(href))
            is_c = "/c/assortiment" in href
            if not (is_h or is_c):
                continue

            # Skip top-level section index pages.
            if any(href.endswith(s) for s in ("/s10008015", "/s10008009")):
                continue

            external_id = self._extract_path_id(href)
            if not external_id or external_id in seen_ids or external_id in _SKIP_IDS:
                continue
            seen_ids.add(external_id)

            self._register_category_url(external_id, href)
            categories.append(
                ScrapedCategory(
                    external_id=external_id,
                    name=html_mod.unescape(label),
                )
            )

        return categories

    def _extract_category_links(
        self,
        page_html: str,
        parent_id: str,
        seen_ids: set[str],
    ) -> list[ScrapedCategory]:
        sub_cats: list[ScrapedCategory] = []
        local_seen: set[str] = set()

        for href, raw_name in _RE_ANCHOR_CAT.findall(page_html):
            external_id = self._extract_path_id(href)
            if not external_id:
                continue
            if external_id in seen_ids or external_id in local_seen:
                continue
            if external_id in _SKIP_IDS:
                continue

            name = html_mod.unescape(raw_name.strip())
            if not name:
                continue

            local_seen.add(external_id)
            self._register_category_url(external_id, href)
            sub_cats.append(
                ScrapedCategory(
                    external_id=external_id,
                    name=name,
                    parent_external_id=parent_id,
                )
            )

        return sub_cats

    def _extract_nuxt_categories(
        self,
        page_html: str,
        parent_id: str,
        seen_ids: set[str],
    ) -> list[ScrapedCategory]:
        sub_cats: list[ScrapedCategory] = []
        local_seen: set[str] = set()

        # Scope search to the __NUXT_DATA__ script block only — avoids running
        # the triplet regex over the entire (potentially multi-MB) page HTML.
        nuxt_match = _RE_NUXT_SCRIPT.search(page_html)
        search_text = nuxt_match.group(1) if nuxt_match else page_html

        for _num_id, raw_name, url in _RE_NUXT_TRIPLET.findall(search_text):
            external_id = self._extract_path_id(url)
            if not external_id:
                continue
            if external_id in seen_ids or external_id in local_seen:
                continue
            if external_id in _SKIP_IDS:
                continue

            name = html_mod.unescape(raw_name.strip())
            if not name:
                continue

            local_seen.add(external_id)
            self._register_category_url(external_id, url)
            sub_cats.append(
                ScrapedCategory(
                    external_id=external_id,
                    name=name,
                    parent_external_id=parent_id,
                )
            )

        return sub_cats

    def _scrape_category_pages(
        self,
        cat_id: str,
        cat_url: str,
        seen: dict[str, ScrapedProduct],
    ) -> None:
        page_step: int | None = None
        offset = 0

        while True:
            fetch_url = cat_url if offset == 0 else f"{cat_url}?offset={offset}"
            try:
                page_html = self._fetch_page(fetch_url)
            except Exception as exc:
                self.logger.warning("Error fetching %s at offset=%d: %s", cat_id, offset, exc)
                break

            grid_products = self._extract_grid_products(page_html)
            if not grid_products:
                break

            # Derive the step from the first successful page.
            if page_step is None:
                page_step = len(grid_products)

            new_count = 0
            for data in grid_products:
                product = self._parse_product(data, category_external_id=cat_id)
                if product and product.external_id not in seen:
                    seen[product.external_id] = product
                    new_count += 1

            self.logger.debug(
                "Category %s offset=%d: %d new / %d total unique",
                cat_id,
                offset,
                new_count,
                len(seen),
            )

            # Stop conditions:
            # 1. Partial page → reached the last page.
            # 2. No new products on a non-first page → server returned same page.
            # 3. Safety ceiling.
            if len(grid_products) < page_step or (new_count == 0 and offset > 0) or offset + page_step > MAX_OFFSET:
                break

            offset += page_step
            time.sleep(REQUEST_DELAY)

    def _scrape_deals_pages(self, seen: dict[str, ScrapedProduct]) -> None:
        page_step: int | None = None
        offset = 0

        while True:
            fetch_url = DEALS_PATH if offset == 0 else f"{DEALS_PATH}?offset={offset}"
            try:
                page_html = self._fetch_page(fetch_url)
            except Exception as exc:
                self.logger.warning("Error fetching deals page at offset=%d: %s", offset, exc)
                break

            deal_products = self._extract_grid_products(page_html)
            if not deal_products:
                break

            if page_step is None:
                page_step = len(deal_products)

            for data in deal_products:
                cat_id = self._match_category(data)
                product = self._parse_product(data, category_external_id=cat_id)
                if product:
                    seen[product.external_id] = product  # Always overwrite.

            self.logger.debug(
                "Deals page offset=%d: %d products / %d total unique",
                offset,
                len(deal_products),
                len(seen),
            )

            if len(deal_products) < page_step or offset + page_step > MAX_OFFSET:
                break

            offset += page_step
            time.sleep(REQUEST_DELAY)

    def _fetch_page(self, url: str) -> str:
        if not url.startswith("http"):
            url = BASE_URL + url
        cached = self._page_cache.get(url)
        if cached is not None:
            return cached
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        self._page_cache[url] = response.text
        return response.text

    def _extract_grid_products(self, page_html: str) -> list[dict]:
        products: list[dict] = []
        for match in _RE_GRID_DATA.findall(page_html):
            try:
                data = json.loads(html_mod.unescape(match))
            except (json.JSONDecodeError, ValueError):
                continue
            if isinstance(data, dict) and "productId" in data:
                products.append(data)
        return products

    def _parse_product(
        self,
        data: dict,
        category_external_id: str | None = None,
    ) -> ScrapedProduct | None:
        product_id = data.get("productId")
        title = data.get("title")
        if not product_id or not title:
            return None

        price_data = data.get("price") or {}
        current_price_val = price_data.get("price")
        old_price_val = price_data.get("oldPrice")
        discount = price_data.get("discount") or {}
        has_discount = bool(discount.get("showDiscount"))

        if has_discount and old_price_val is not None:
            base_price = Decimal(str(old_price_val))
            current_price = Decimal(str(current_price_val)) if current_price_val is not None else None
        elif current_price_val is not None:
            base_price = Decimal(str(current_price_val))
            current_price = base_price
        else:
            # Product is in the assortment but currently has no listed price.
            base_price = None
            current_price = None

        discount_text: str | None = None
        pct = discount.get("percentageDiscount")
        if has_discount and pct:
            discount_text = f"{pct}% korting"

        image_url = data.get("image")
        canonical_path = data.get("canonicalPath")
        website_url = BASE_URL + canonical_path if canonical_path else None

        return ScrapedProduct(
            external_id=str(product_id),
            name=title,
            base_price=base_price,
            current_price=current_price,
            has_discount=has_discount,
            discount_text=discount_text,
            image_url=image_url if isinstance(image_url, str) else None,
            website_url=website_url,
            category_external_id=category_external_id,
        )

    def _match_category(self, data: dict) -> str | None:
        keyfacts = data.get("keyfacts") or {}
        won_category = keyfacts.get("wonCategoryPrimary")
        if not isinstance(won_category, str):
            return None

        # wonCategoryPrimary: "Werelden van nood/Eten en …/Groenten & fruit"
        # Walk from most-specific to least-specific segment for best match.
        segments = [s.strip() for s in won_category.split("/")]
        for segment in reversed(segments):
            clean = _RE_BRACKET_SUFFIX.sub("", segment).strip()
            cat_id = self._category_name_to_id.get(clean)
            if cat_id:
                return cat_id

        return None

    def _register_category_url(self, external_id: str, href: str) -> None:
        clean_url = urlparse(href)._replace(query="", fragment="").geturl()
        self._category_urls[external_id] = clean_url

    @staticmethod
    def _extract_path_id(url: str) -> str | None:
        parsed = urlparse(url)
        match = _RE_PATH_ID.search(parsed.path)
        return match.group(1) if match else None

    def close(self) -> None:
        self.session.close()
        self._category_urls.clear()
        self._category_name_to_id.clear()
        self._page_cache.clear()
