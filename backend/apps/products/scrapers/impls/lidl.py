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

# Lidl category pages paginate via ?offset=N (24 items per page).
PAGE_SIZE = 24
# Safety ceiling: never paginate beyond this offset for a single category.
MAX_OFFSET = PAGE_SIZE * 100  # 2400 products per category

# Polite delay between consecutive HTTP requests.
REQUEST_DELAY = 0.5

# Top-level section pages (not product categories — do not treat as leaves).
_SECTION_IDS = frozenset(["s10008015", "s10008009"])


@register_scraper
class LidlScraper(BaseSupermarketScraper):
    """Scraper for Lidl Netherlands (www.lidl.nl).

    Strategy
    --------
    1. ``scrape_categories()``
       • Fetches the main assortment page and extracts top-level categories
         using two fallback methods (card-list cards, then nav links).
       • For every discovered category page it visits the page and looks for
         additional sub-category links, recursively, until no new IDs are found.
       • All category URLs are stored in ``_category_urls`` for use by
         ``scrape_products()``.

    2. ``scrape_products()``
       • Iterates over every category URL and paginates through it using
         ``?offset=N`` until no new products appear.
       • As a final pass it also paginates through the deals page so that
         products with live discount pricing overwrite the assortment versions.
       • Global deduplication is by ``productId``; the first category where a
         product is seen determines its ``category_external_id``.
    """

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
        # external_id → clean path/URL for every discovered category page.
        self._category_urls: dict[str, str] = {}
        # name → external_id mapping used to match deal products to categories.
        self._category_name_to_id: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Public scraper interface
    # ------------------------------------------------------------------

    def scrape_categories(self) -> list[ScrapedCategory]:
        categories: list[ScrapedCategory] = []
        seen_ids: set[str] = set()

        # Step 1: Extract top-level categories from the main assortment page.
        assortment_html = self._fetch_page(ASSORTMENT_PATH)
        top_level = self._extract_card_list_categories(assortment_html)
        if not top_level:
            top_level = self._extract_nav_categories(assortment_html)

        for cat in top_level:
            if cat.external_id not in seen_ids:
                seen_ids.add(cat.external_id)
                categories.append(cat)

        # Step 2: Recursively discover sub-categories from every category page.
        # We use a BFS queue; new sub-categories are appended and visited in turn.
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
                    "Error fetching category page %s (%s): %s",
                    parent_cat.external_id,
                    cat_url,
                    exc,
                )
                continue

            sub_cats = self._extract_category_links(
                page_html,
                parent_id=parent_cat.external_id,
                seen_ids=seen_ids,
            )
            for sub_cat in sub_cats:
                seen_ids.add(sub_cat.external_id)
                categories.append(sub_cat)
                queue.append(sub_cat)

        self._category_name_to_id = {c.name: c.external_id for c in categories}
        self.logger.info("Scraped %d categories", len(categories))
        return categories

    def scrape_products(self) -> list[ScrapedProduct]:
        # Maps external_id → ScrapedProduct; last writer wins for deal products.
        seen: dict[str, ScrapedProduct] = {}

        # Pass 1: paginate through every known category page.
        for cat_id, cat_url in self._category_urls.items():
            self._scrape_category_pages(cat_id, cat_url, seen)

        # Pass 2: paginate through the deals page.
        # Deal products have live pricing; they overwrite the assortment versions.
        self._scrape_deals_pages(seen)

        products = list(seen.values())
        self.logger.info("Scraped %d unique products in total", len(products))
        return products

    # ------------------------------------------------------------------
    # Category extraction helpers
    # ------------------------------------------------------------------

    def _extract_card_list_categories(self, page_html: str) -> list[ScrapedCategory]:
        """Extract categories from ATheContentPageCardList cards (legacy layout)."""
        categories: list[ScrapedCategory] = []
        pattern = (
            r'ATheContentPageCardList__Item--linked"\s+'
            r'href="([^"]+)"\s+'
            r'data-unified-click="([^"]+)"'
        )
        for href, click_data_encoded in re.findall(pattern, page_html):
            try:
                click_data = json.loads(unquote(click_data_encoded))
            except (json.JSONDecodeError, ValueError):
                continue

            name = click_data.get("linkName")
            if not name:
                continue

            external_id = self._extract_path_id(href)
            if not external_id:
                continue

            self._register_category_url(external_id, href)
            categories.append(
                ScrapedCategory(external_id=external_id, name=html_mod.unescape(name))
            )

        return categories

    def _extract_nav_categories(self, page_html: str) -> list[ScrapedCategory]:
        """Extract categories from sidebar / nav links (fallback layout)."""
        categories: list[ScrapedCategory] = []
        seen_ids: set[str] = set()
        # Match any link that carries a Google-Analytics label attribute.
        pattern = r'href="([^"]+)"[^>]*data-ga-label="([^"]+)"'

        for href, label in re.findall(pattern, page_html):
            # Only follow category-level paths.
            if not re.search(r"/c/[^/]+/[as]\d+", href):
                continue
            # Skip top-level section index pages.
            if any(href.endswith(s) for s in ("/s10008015", "/s10008009")):
                continue

            external_id = self._extract_path_id(href)
            if not external_id or external_id in seen_ids:
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
        """Discover sub-category links within any category page.

        Looks for ``<a href="/c/…/a…">Name</a>`` anchors that have not yet been
        seen, registers their URLs and returns ``ScrapedCategory`` objects.
        """
        sub_cats: list[ScrapedCategory] = []
        # Local set prevents returning duplicates within a single page.
        local_seen: set[str] = set()

        # Broad pattern: any anchor whose href is a /c/ category path.
        # The path ID must start with 'a' or 's' followed by digits.
        pattern = r'href="(/c/[^"?#]+/[as]\d+[^"]*)"[^>]*>([^<]{1,100})<'

        for href, raw_name in re.findall(pattern, page_html):
            external_id = self._extract_path_id(href)
            if not external_id:
                continue
            if external_id in seen_ids or external_id in local_seen:
                continue
            if external_id in _SECTION_IDS:
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

    # ------------------------------------------------------------------
    # Product scraping helpers
    # ------------------------------------------------------------------

    def _scrape_category_pages(
        self,
        cat_id: str,
        cat_url: str,
        seen: dict[str, ScrapedProduct],
    ) -> None:
        """Paginate through all pages of a category, adding new products to *seen*."""
        offset = 0
        while True:
            if offset > 0:
                time.sleep(REQUEST_DELAY)

            fetch_url = cat_url if offset == 0 else f"{cat_url}?offset={offset}"
            try:
                page_html = self._fetch_page(fetch_url)
            except Exception as exc:
                self.logger.warning(
                    "Error fetching %s at offset=%d: %s", cat_id, offset, exc
                )
                break

            grid_products = self._extract_grid_products(page_html)
            if not grid_products:
                # Empty page — this category is fully scraped.
                break

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

            if new_count == 0 or offset >= MAX_OFFSET:
                # Either no new products on this page, or we hit the safety limit.
                break

            offset += PAGE_SIZE

    def _scrape_deals_pages(self, seen: dict[str, ScrapedProduct]) -> None:
        """Paginate through the deals page and upsert products with live pricing."""
        offset = 0
        while True:
            if offset > 0:
                time.sleep(REQUEST_DELAY)

            fetch_url = DEALS_PATH if offset == 0 else f"{DEALS_PATH}?offset={offset}"
            try:
                page_html = self._fetch_page(fetch_url)
            except Exception as exc:
                self.logger.warning(
                    "Error fetching deals page at offset=%d: %s", offset, exc
                )
                break

            deal_products = self._extract_grid_products(page_html)
            if not deal_products:
                break

            new_count = 0
            for data in deal_products:
                cat_id = self._match_category(data)
                product = self._parse_product(data, category_external_id=cat_id)
                if product:
                    is_new = product.external_id not in seen
                    seen[product.external_id] = product  # Always overwrite with deal data.
                    if is_new:
                        new_count += 1

            self.logger.debug(
                "Deals page offset=%d: %d new / %d total unique",
                offset,
                new_count,
                len(seen),
            )

            if len(deal_products) < PAGE_SIZE or offset >= MAX_OFFSET:
                # Received a partial page — this is the last page.
                break

            offset += PAGE_SIZE

    # ------------------------------------------------------------------
    # Low-level fetch / parse utilities
    # ------------------------------------------------------------------

    def _fetch_page(self, url: str) -> str:
        if not url.startswith("http"):
            url = BASE_URL + url
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        return response.text

    def _extract_grid_products(self, page_html: str) -> list[dict]:
        """Return all product dicts embedded as ``data-grid-data`` attributes."""
        products: list[dict] = []
        for match in re.findall(r'data-grid-data="([^"]*?)"', page_html):
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
            current_price = (
                Decimal(str(current_price_val)) if current_price_val is not None else None
            )
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
        """Match a deal product to a known category via ``wonCategoryPrimary``."""
        keyfacts = data.get("keyfacts") or {}
        won_category = keyfacts.get("wonCategoryPrimary")
        if not isinstance(won_category, str):
            return None

        # wonCategoryPrimary looks like "Werelden van nood/Eten en …/Groenten & fruit".
        # Try the last segment first, then progressively shorter suffixes.
        segments = [s.strip() for s in won_category.split("/")]
        for segment in reversed(segments):
            # Strip parenthetical qualifiers such as "(Diepvriesvoeding)".
            clean = re.sub(r"\s*\(.*?\)\s*$", "", segment).strip()
            cat_id = self._category_name_to_id.get(clean)
            if cat_id:
                return cat_id

        return None

    # ------------------------------------------------------------------
    # Misc utilities
    # ------------------------------------------------------------------

    def _register_category_url(self, external_id: str, href: str) -> None:
        """Store the clean (query-free) URL for a category ID."""
        clean_url = urlparse(href)._replace(query="", fragment="").geturl()
        self._category_urls[external_id] = clean_url

    @staticmethod
    def _extract_path_id(url: str) -> str | None:
        """Extract the path segment ID (e.g. ``a10008017`` or ``s10052442``)."""
        parsed = urlparse(url)
        match = re.search(r"/([as]\d+)(?:[/?#]|$)", parsed.path)
        return match.group(1) if match else None

    def close(self) -> None:
        self.session.close()
