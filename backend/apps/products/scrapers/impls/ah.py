from decimal import Decimal

import requests

from products.scrapers.base import BaseSupermarketScraper
from products.scrapers.dtos import ScrapedCategory, ScrapedProduct
from products.scrapers.registry import register_scraper

PAGE_SIZE = 1000
# NL-specific API domain (Belgian AH uses api.ah.be).
BASE_URL = "https://api.ah.nl"
PRODUCT_URL = "https://www.ah.nl/producten/product/wi{webshop_id}"


@register_scraper
class AlbertHeijnScraper(BaseSupermarketScraper):
    supermarket_slug = "ah"

    def __init__(self):
        super().__init__()
        self.session = requests.Session()
        # Mimic the AH mobile app ("Appie") to access the undocumented API.
        self.session.headers.update(
            {
                "User-Agent": "Appie/8.22.3",  # AH mobile app identifier
                "Content-Type": "application/json",
                "x-application": "AHWEBSHOP",  # Selects the online webshop context
            }
        )
        self._category_name_to_id: dict[str, str] = {}
        # Maps main category ID -> list of (sub_category_name, sub_category_id).
        self._main_to_subs: dict[str, list[tuple[str, str]]] = {}
        self._authenticate()

    def _authenticate(self):
        response = self.session.post(
            f"{BASE_URL}/mobile-auth/v1/auth/token/anonymous",
            json={"clientId": "appie"},
        )
        response.raise_for_status()
        token = response.json()["access_token"]
        self.session.headers["Authorization"] = f"Bearer {token}"
        self.logger.info("Authenticated with AH API")

    def scrape_categories(self) -> list[ScrapedCategory]:
        response = self.session.get(f"{BASE_URL}/mobile-services/v1/product-shelves/categories")
        response.raise_for_status()
        main_categories = response.json()

        categories: list[ScrapedCategory] = []

        for main in main_categories:
            main_id = str(main["id"])
            categories.append(ScrapedCategory(external_id=main_id, name=main["name"]))

            sub_response = self.session.get(
                f"{BASE_URL}/mobile-services/v1/product-shelves/categories/{main_id}/sub-categories"
            )
            sub_response.raise_for_status()
            children = sub_response.json().get("children", [])

            for child in children:
                categories.append(
                    ScrapedCategory(
                        external_id=str(child["id"]),
                        name=child["name"],
                        parent_external_id=main_id,
                    )
                )

        self._category_name_to_id = {c.name: c.external_id for c in categories}
        # Build main->subs lookup for fuzzy sub-category matching.
        for cat in categories:
            if cat.parent_external_id:
                self._main_to_subs.setdefault(cat.parent_external_id, []).append((cat.name, cat.external_id))
        self.logger.info("Scraped %d categories", len(categories))
        return categories

    def scrape_products(self) -> list[ScrapedProduct]:
        taxonomy_ids = self._get_taxonomy_ids()
        self.logger.info("Found %d taxonomy categories to scrape", len(taxonomy_ids))

        seen: set[int] = set()
        products: list[ScrapedProduct] = []

        for taxonomy_id in taxonomy_ids:
            page = 0
            while True:
                params = {
                    "sortOn": "RELEVANCE",
                    "page": page,
                    "size": PAGE_SIZE,
                    "taxonomyId": taxonomy_id,
                }
                response = self.session.get(
                    f"{BASE_URL}/mobile-services/product/search/v2",
                    params=params,
                )
                response.raise_for_status()
                data = response.json()

                for item in data.get("products", []):
                    webshop_id = item["webshopId"]
                    if webshop_id in seen:
                        continue
                    seen.add(webshop_id)
                    products.append(self._parse_product(item))

                total_pages = data["page"]["totalPages"]
                page += 1
                if page >= total_pages:
                    break

        self.logger.info("Scraped %d products", len(products))
        return products

    def _get_taxonomy_ids(self) -> list[str]:
        response = self.session.get(
            f"{BASE_URL}/mobile-services/product/search/v2",
            params={"sortOn": "RELEVANCE", "page": 0, "size": 1},
        )
        response.raise_for_status()
        data = response.json()

        for f in data.get("filters", []):
            if f.get("id") == "taxonomy":
                return [option["id"] for option in f["options"]]
        return []

    def _parse_product(self, item: dict) -> ScrapedProduct:
        price_before = item.get("priceBeforeBonus")
        current_price = item.get("currentPrice", price_before)
        is_bonus = item.get("isBonus", False)

        images = item.get("images", [])
        image_url = images[0]["url"] if images else None

        webshop_id = item["webshopId"]

        category_external_id = self._match_category(item.get("mainCategory"), item.get("subCategory"))

        return ScrapedProduct(
            external_id=str(webshop_id),
            name=item["title"],
            base_price=Decimal(str(price_before)) if price_before is not None else None,
            current_price=Decimal(str(current_price)) if current_price is not None else None,
            has_discount=is_bonus,
            discount_text=item.get("bonusMechanism") or None,
            image_url=image_url,
            website_url=PRODUCT_URL.format(webshop_id=webshop_id),
            category_external_id=category_external_id,
        )

    def _match_category(self, main_category: str | None, sub_category: str | None) -> str | None:
        """Match a product to its deepest category.

        The product API returns e.g. subCategory="Komkommer" while the category
        API has group names like "Komkommer, tomaten, avocado". We find the
        sub-category whose name contains the product's subCategory value.
        Falls back to mainCategory if no sub-category match is found.
        """
        main_id = self._category_name_to_id.get(main_category) if main_category else None

        if sub_category and main_id:
            # Try exact match first.
            exact = self._category_name_to_id.get(sub_category)
            if exact:
                return exact
            # Find a sub-category whose name contains the product's subCategory.
            sub_lower = sub_category.lower()
            for cat_name, cat_id in self._main_to_subs.get(main_id, []):
                if sub_lower in cat_name.lower():
                    return cat_id

        return main_id

    def close(self):
        self.session.close()
