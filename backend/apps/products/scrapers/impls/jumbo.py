import json
import re
from decimal import Decimal

import requests

from products.scrapers.base import BaseSupermarketScraper
from products.scrapers.dtos import ScrapedCategory, ScrapedProduct
from products.scrapers.registry import register_scraper

PAGE_SIZE = 24
PRODUCTS_PATH = "/producten/"
BASE_URL = "https://www.jumbo.com"


@register_scraper
class JumboScraper(BaseSupermarketScraper):
    supermarket_slug = "jumbo"

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
        # Pin locale to Netherlands (Jumbo also serves Belgium via nl-BE).
        self.session.cookies.set("i18n_redirected", "nl-NL", domain="www.jumbo.com")
        self._category_name_to_id: dict[str, str] = {}
        self._leaf_category_urls: list[tuple[str, str]] = []

    def _scrape_sub_categories(self, parent_id: str, parent_url: str) -> list[ScrapedCategory]:
        data = self._fetch_search_data(parent_url)
        tiles = self._extract_category_tiles(data)
        if not tiles:
            self._leaf_category_urls.append((parent_id, parent_url))
            return []

        sub_categories: list[ScrapedCategory] = []
        for tile in tiles:
            friendly_url = tile.get("friendlyUrl", "")
            sub_category = ScrapedCategory(
                external_id=tile["catId"],
                name=tile["name"],
                parent_external_id=parent_id,
            )
            sub_categories.append(sub_category)
            if friendly_url:
                sub_categories.extend(
                    self._scrape_sub_categories(sub_category.external_id, PRODUCTS_PATH + friendly_url)
                )
        return sub_categories

    def scrape_categories(self) -> list[ScrapedCategory]:
        main_data = self._fetch_search_data(PRODUCTS_PATH)
        main_tiles = self._extract_category_tiles(main_data)
        categories: list[ScrapedCategory] = []

        for tile in main_tiles:
            cat_id = tile["catId"]
            friendly_url = tile.get("friendlyUrl", "")

            # Skip non-product categories (e.g. "Eerder gekocht").
            if not friendly_url or "custom-category" in cat_id:
                continue

            categories.append(ScrapedCategory(external_id=cat_id, name=tile["name"]))
            categories.extend(self._scrape_sub_categories(cat_id, PRODUCTS_PATH + friendly_url))

        self._category_name_to_id = {c.name: c.external_id for c in categories}
        self.logger.info(
            "Scraped %d categories (%d leaf category URLs)",
            len(categories),
            len(self._leaf_category_urls),
        )
        return categories

    def scrape_products(self) -> list[ScrapedProduct]:
        seen: set[str] = set()
        products: list[ScrapedProduct] = []
        self.logger.info("Scraping products from %d leaf category pages", len(self._leaf_category_urls))

        for cat_id, cat_url in self._leaf_category_urls:
            first_data = self._fetch_search_data(cat_url)
            total_count = self._extract_count(first_data)
            self._collect_products(first_data, seen, products, category_id_override=cat_id)

            offset = PAGE_SIZE
            while offset < total_count:
                page_data = self._fetch_search_data(f"{cat_url}?offSet={offset}")
                self._collect_products(page_data, seen, products, category_id_override=cat_id)
                offset += PAGE_SIZE

            if len(products) % 500 < PAGE_SIZE:
                self.logger.info("Scraped %d products so far", len(products))

        self.logger.info("Scraped %d products", len(products))
        return products

    def _fetch_search_data(self, path: str) -> list:
        """Fetch a Jumbo page and extract the Nuxt SSR payload."""
        url = BASE_URL + path if not path.startswith("http") else path
        response = self.session.get(url)
        response.raise_for_status()

        match = re.search(
            r'id="__NUXT_DATA__"[^>]*>(.*?)</script>',
            response.text,
            re.DOTALL,
        )
        if not match:
            raise ValueError(f"No __NUXT_DATA__ found in {url}")

        return json.loads(match.group(1))

    def _unwrap(self, data: list, idx):
        """Unwrap Nuxt Ref/Reactive/EmptyRef wrappers to get the actual value."""
        if not isinstance(idx, int) or idx >= len(data):
            return idx
        val = data[idx]
        if isinstance(val, list) and len(val) == 2 and isinstance(val[0], str):
            if val[0] in ("Reactive", "Ref", "EmptyRef"):
                return self._unwrap(data, val[1])
        return val

    def _resolve(self, data: list, idx, depth: int = 0):
        """Recursively resolve Nuxt data references into a plain Python object."""
        if depth > 12 or not isinstance(idx, int) or idx >= len(data):
            return idx
        val = data[idx]
        if isinstance(val, dict):
            return {k: self._resolve(data, v, depth + 1) for k, v in val.items()}
        if isinstance(val, list):
            if len(val) == 2 and isinstance(val[0], str) and val[0] in ("Reactive", "Ref", "EmptyRef"):
                return self._resolve(data, val[1], depth + 1)
            return [self._resolve(data, v, depth + 1) for v in val]
        return val

    def _find_search_result(self, data: list) -> dict | None:
        """Find the searchProducts result dict in the Nuxt data array."""
        for item in data:
            if isinstance(item, dict) and "products" in item and "count" in item and "start" in item and len(item) > 10:
                return item
        return None

    def _extract_category_tiles(self, data: list) -> list[dict]:
        """Extract category tiles from Nuxt SSR data."""
        result = self._find_search_result(data)
        if not result:
            return []

        tiles_idx = result.get("categoryTiles")
        tiles = self._unwrap(data, tiles_idx)
        if not isinstance(tiles, list):
            return []

        resolved = []
        for idx in tiles:
            tile = self._resolve(data, idx) if isinstance(idx, int) else idx
            if isinstance(tile, dict) and "catId" in tile:
                resolved.append(tile)
        return resolved

    def _extract_count(self, data: list) -> int:
        """Extract the total product count from Nuxt SSR data."""
        result = self._find_search_result(data)
        if not result:
            return 0
        count = self._unwrap(data, result["count"])
        return int(count) if isinstance(count, (int, float)) else 0

    def _collect_products(
        self,
        data: list,
        seen: set[str],
        products: list[ScrapedProduct],
        category_id_override: str | None = None,
    ):
        """Parse products from a page's Nuxt data and append to the list."""
        result = self._find_search_result(data)
        if not result:
            return

        product_list = self._unwrap(data, result["products"])
        if not isinstance(product_list, list):
            return

        for idx in product_list:
            if not isinstance(idx, int) or idx >= len(data):
                continue
            raw = data[idx]
            if not isinstance(raw, dict) or "id" not in raw:
                continue

            product_id = self._unwrap(data, raw["id"])
            if not isinstance(product_id, str) or product_id in seen:
                continue
            seen.add(product_id)

            product = self._parse_product(data, raw, product_id, category_id_override)
            if product:
                products.append(product)

    def _parse_product(
        self,
        data: list,
        raw: dict,
        product_id: str,
        category_id_override: str | None = None,
    ) -> ScrapedProduct | None:
        """Parse a single product from raw Nuxt data references."""
        title = self._unwrap(data, raw.get("title"))
        if not isinstance(title, str):
            return None

        # Resolve prices (in cents).
        prices = self._resolve(data, raw.get("prices"))
        base_price_cents = prices.get("price") if isinstance(prices, dict) else None
        promo_price_cents = prices.get("promoPrice") if isinstance(prices, dict) else None

        base_price = self._cents_to_decimal(base_price_cents) if isinstance(base_price_cents, (int, float)) else None
        has_discount = promo_price_cents is not None and isinstance(promo_price_cents, (int, float))
        current_price = self._cents_to_decimal(promo_price_cents) if has_discount else base_price

        # Discount text from promotion tags.
        discount_text = None
        promotions = self._resolve(data, raw.get("promotions"))
        if isinstance(promotions, list) and len(promotions) > 0:
            promo = promotions[0]
            if isinstance(promo, dict):
                tags = promo.get("tags", [])
                if isinstance(tags, list) and len(tags) > 0 and isinstance(tags[0], dict):
                    discount_text = tags[0].get("text")

        image = self._unwrap(data, raw.get("image"))
        link = self._unwrap(data, raw.get("link"))
        if category_id_override:
            category_external_id = category_id_override
        else:
            category_name = self._unwrap(data, raw.get("category"))
            category_external_id = (
                self._category_name_to_id.get(category_name) if isinstance(category_name, str) else None
            )

        return ScrapedProduct(
            external_id=product_id,
            name=title,
            base_price=base_price,
            current_price=current_price,
            has_discount=has_discount,
            discount_text=discount_text,
            image_url=image if isinstance(image, str) else None,
            website_url=BASE_URL + link if isinstance(link, str) else None,
            category_external_id=category_external_id,
        )

    @staticmethod
    def _cents_to_decimal(cents: int | float) -> Decimal:
        """Convert a price in cents to a Decimal in euros."""
        return Decimal(cents) / Decimal(100)

    def close(self):
        self.session.close()
