import html as html_mod
import json
import re
from decimal import Decimal
from urllib.parse import unquote, urlparse

import requests

from products.scrapers.base import BaseSupermarketScraper
from products.scrapers.dtos import ScrapedCategory, ScrapedProduct
from products.scrapers.registry import register_scraper

BASE_URL = "https://www.lidl.nl"
DEALS_PATH = "/c/aanbiedingen/a10008785"
ASSORTMENT_PATH = "/c/assortiment-producten/s10008015"


@register_scraper
class LidlScraper(BaseSupermarketScraper):
    supermarket_slug = "lidl"

    def __init__(self):
        super().__init__()
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "nl-NL,nl;q=0.9",
            }
        )
        self._category_name_to_id: dict[str, str] = {}
        self._category_urls: list[tuple[str, str]] = []

    def scrape_categories(self) -> list[ScrapedCategory]:
        page_html = self._fetch_page(ASSORTMENT_PATH)
        categories: list[ScrapedCategory] = []

        categories = self._extract_card_list_categories(page_html)
        if not categories:
            categories = self._extract_nav_categories(page_html)

        self._category_name_to_id = {c.name: c.external_id for c in categories}
        self.logger.info("Scraped %d categories", len(categories))
        return categories

    def _extract_card_list_categories(self, page_html: str) -> list[ScrapedCategory]:
        """Extract categories from ATheContentPageCardList cards (legacy layout)."""
        categories: list[ScrapedCategory] = []
        pattern = r'ATheContentPageCardList__Item--linked"\s+' r'href="([^"]+)"\s+' r'data-unified-click="([^"]+)"'
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

            categories.append(ScrapedCategory(external_id=external_id, name=html_mod.unescape(name)))
            clean_url = urlparse(href)._replace(query="", fragment="").geturl()
            self._category_urls.append((external_id, clean_url))

        return categories

    def _extract_nav_categories(self, page_html: str) -> list[ScrapedCategory]:
        """Extract food categories from sidebar navigation links."""
        categories: list[ScrapedCategory] = []
        pattern = r'href="([^"]+)"[^>]*data-ga-label="([^"]+)"'
        seen_ids: set[str] = set()

        for href, label in re.findall(pattern, page_html):
            # Only include assortment sub-category pages, not generic nav links.
            if "/c/assortiment" not in href and "/c/assortiment-supermarkt" not in href:
                continue
            # Skip the index pages themselves.
            if href.endswith(("/s10008015", "/s10008009")):
                continue

            external_id = self._extract_path_id(href)
            if not external_id or external_id in seen_ids:
                continue
            seen_ids.add(external_id)

            name = html_mod.unescape(label)
            categories.append(ScrapedCategory(external_id=external_id, name=name))
            clean_url = urlparse(href)._replace(query="", fragment="").geturl()
            self._category_urls.append((external_id, clean_url))

        return categories

    def scrape_products(self) -> list[ScrapedProduct]:
        seen: dict[str, ScrapedProduct] = {}

        # 1. Assortment products from each category page (no prices).
        for cat_id, cat_url in self._category_urls:
            page_html = self._fetch_page(cat_url)
            grid_products = self._extract_grid_products(page_html)

            for data in grid_products:
                product = self._parse_product(data, category_external_id=cat_id)
                if product and product.external_id not in seen:
                    seen[product.external_id] = product

            self.logger.info("Category %s: %d products (total: %d)", cat_id, len(grid_products), len(seen))

        # 2. Deal products (have prices) — overwrite assortment versions.
        deals_html = self._fetch_page(DEALS_PATH)
        deal_products = self._extract_grid_products(deals_html)

        for data in deal_products:
            category_external_id = self._match_category(data)
            product = self._parse_product(data, category_external_id=category_external_id)
            if product:
                seen[product.external_id] = product

        self.logger.info("Deals page: %d products (total unique: %d)", len(deal_products), len(seen))

        products = list(seen.values())
        self.logger.info("Scraped %d products", len(products))
        return products

    def _fetch_page(self, url: str) -> str:
        if not url.startswith("http"):
            url = BASE_URL + url
        response = self.session.get(url)
        response.raise_for_status()
        return response.text

    def _extract_grid_products(self, page_html: str) -> list[dict]:
        products = []
        for match in re.findall(r'data-grid-data="([^"]*?)"', page_html):
            try:
                data = json.loads(html_mod.unescape(match))
            except (json.JSONDecodeError, ValueError):
                continue
            if isinstance(data, dict) and "productId" in data:
                products.append(data)
        return products

    def _parse_product(self, data: dict, category_external_id: str | None = None) -> ScrapedProduct | None:
        product_id = data.get("productId")
        title = data.get("title")
        if not product_id or not title:
            return None

        price_data = data.get("price", {})
        current_price_val = price_data.get("price")
        old_price_val = price_data.get("oldPrice")
        discount = price_data.get("discount", {})

        has_discount = bool(discount.get("showDiscount"))

        if has_discount and old_price_val is not None:
            base_price = Decimal(str(old_price_val))
            current_price = Decimal(str(current_price_val)) if current_price_val is not None else None
        elif current_price_val is not None:
            base_price = Decimal(str(current_price_val))
            current_price = base_price
        else:
            base_price = None
            current_price = None

        discount_text = None
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
        """Match a deal product to a category via wonCategoryPrimary."""
        keyfacts = data.get("keyfacts", {})
        won_category = keyfacts.get("wonCategoryPrimary")
        if not isinstance(won_category, str):
            return None

        # wonCategoryPrimary looks like "Werelden van nood/Eten en .../Groenten & fruit"
        # Try matching the last segment against known category names.
        last_segment = won_category.rsplit("/", 1)[-1].strip()
        # Remove parenthetical suffixes like "(Diepvriesvoeding)"
        last_segment = re.sub(r"\s*\(.*?\)\s*$", "", last_segment)

        return self._category_name_to_id.get(last_segment)

    @staticmethod
    def _extract_path_id(url: str) -> str | None:
        """Extract the path ID (e.g. 'a10008017' or 's10052442') from a Lidl URL."""
        parsed = urlparse(url)
        match = re.search(r"/([as]\d+)(?:\?|$)", parsed.path)
        return match.group(1) if match else None

    def close(self):
        self.session.close()
