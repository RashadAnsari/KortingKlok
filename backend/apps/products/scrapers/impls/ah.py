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
        self._leaf_category_ids: list[str] = []
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
        for main_category in main_categories:
            scraped_category = ScrapedCategory(
                name=main_category["name"],
                external_id=str(main_category["id"]),
            )
            categories.append(scraped_category)
            categories.extend(self._scrape_sub_categories(scraped_category.external_id))
            self.logger.info("Scraped category '%s' with ID %s", scraped_category.name, scraped_category.external_id)

        self._category_name_to_id = {c.name: c.external_id for c in categories}
        self.logger.info("Scraped %d categories (%d leaf categories)", len(categories), len(self._leaf_category_ids))
        return categories

    def _scrape_sub_categories(self, parent_id: str) -> list[ScrapedCategory]:
        sub_response = self.session.get(
            f"{BASE_URL}/mobile-services/v1/product-shelves/categories/{parent_id}/sub-categories"
        )
        sub_response.raise_for_status()
        children = sub_response.json().get("children", [])
        if len(children) == 0:
            self._leaf_category_ids.append(parent_id)
            return []

        sub_categories: list[ScrapedCategory] = []
        for child in children:
            sub_category = ScrapedCategory(
                name=child["name"],
                external_id=str(child["id"]),
                parent_external_id=parent_id,
            )
            sub_categories.append(sub_category)
            sub_categories.extend(self._scrape_sub_categories(sub_category.external_id))
        return sub_categories

    def scrape_products(self) -> list[ScrapedProduct]:
        self.logger.info("Scraping products from %d leaf categories", len(self._leaf_category_ids))

        seen: set[int] = set()
        products: list[ScrapedProduct] = []

        for taxonomy_id in self._leaf_category_ids:
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

            self.logger.info("Scraped %d products from category ID %s", len(seen), taxonomy_id)

        self.logger.info("Scraped %d products", len(products))
        return products

    def _parse_product(self, item: dict) -> ScrapedProduct:
        price_before = item.get("priceBeforeBonus")
        current_price = item.get("currentPrice", price_before)
        is_bonus = item.get("isBonus", False)

        images = item.get("images", [])
        image_url = images[0]["url"] if images else None

        webshop_id = item["webshopId"]

        sub_category = item.get("subCategory")
        main_category = item.get("mainCategory")
        category_external_id = self._category_name_to_id.get(sub_category) or self._category_name_to_id.get(
            main_category
        )

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

    def close(self):
        self.session.close()
