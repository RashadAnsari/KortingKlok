from decimal import Decimal

import requests

from products.scrapers.base import BaseSupermarketScraper
from products.scrapers.dtos import ScrapedCategory, ScrapedProduct
from products.scrapers.registry import register_scraper

PAGE_SIZE = 24
BASE_URL = "https://www.jumbo.com"
GRAPHQL_URL = "https://www.jumbo.com/api/graphql"

_CATEGORIES_TREE_QUERY = """
query CategoriesTree($exclusions: [String!], $depth: Int = 2) {
  categoriesTree(exclusions: $exclusions, depth: $depth) {
    title: name link: seoURL
    subpages: children {
      title: name link: seoURL
    }
  }
}
"""

_SEARCH_PRODUCTS_QUERY = """
query SearchProducts($input: ProductSearchInput!) {
  searchProducts(input: $input) {
    count
    products {
      id: sku
      title
      image
      link
      prices: price {
        price
        promoPrice
      }
      promotions {
        tags {
          text
        }
      }
    }
  }
}
"""

_GRAPHQL_HEADERS = {
    "Content-Type": "application/json",
    "apollographql-client-version": "master-v30.4.0-web",
}


@register_scraper
class JumboScraper(BaseSupermarketScraper):
    supermarket_slug = "jumbo"

    def __init__(self):
        super().__init__()
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
                "Accept": "*/*",
                "Accept-Language": "nl-NL,nl;q=0.9",
            }
        )
        # Pin locale to Netherlands (Jumbo also serves Belgium via nl-BE).
        self.session.cookies.set("i18n_redirected", "nl-NL", domain="www.jumbo.com")
        self.session.cookies.set("language", "nl_nl", domain="www.jumbo.com")
        self.session.cookies.set("country", "NL", domain="www.jumbo.com")
        self._leaf_category_urls: list[tuple[str, str]] = []

    def scrape_categories(self) -> list[ScrapedCategory]:
        response = self.session.post(
            GRAPHQL_URL,
            json={"operationName": "CategoriesTree", "variables": {}, "query": _CATEGORIES_TREE_QUERY},
            headers={**_GRAPHQL_HEADERS, "apollographql-client-name": "JUMBO_WEB-cms", "x-source": "JUMBO_WEB-cms"},
        )
        response.raise_for_status()
        main_cats = response.json()["data"]["categoriesTree"]

        categories: list[ScrapedCategory] = []
        for main in main_cats:
            main_id = main["link"].removeprefix("/producten/").strip("/")
            categories.append(ScrapedCategory(external_id=main_id, name=main["title"]))
            for sub in main.get("subpages") or []:
                sub_id = sub["link"].removeprefix("/producten/").strip("/")
                categories.append(ScrapedCategory(external_id=sub_id, name=sub["title"], parent_external_id=main_id))
                self._leaf_category_urls.append((sub_id, sub["link"]))
        return categories

    def scrape_products(self) -> list[ScrapedProduct]:
        seen: set[str] = set()
        products: list[ScrapedProduct] = []
        last_logged = 0

        for cat_id, cat_url in self._leaf_category_urls:
            result = self._fetch_products_page(cat_url, 0)
            total_count = result.get("count") or 0
            self._collect_products(result, seen, products, cat_id)

            offset = PAGE_SIZE
            while offset < total_count:
                result = self._fetch_products_page(cat_url, offset)
                self._collect_products(result, seen, products, cat_id)
                offset += PAGE_SIZE

            if len(products) - last_logged >= 1000:
                self.logger.info("Scraped %d products so far", len(products))
                last_logged = len(products)
        return products

    def _fetch_products_page(self, cat_url: str, offset: int) -> dict:
        friendly = cat_url.removeprefix("/producten/").rstrip("/") + f"/?offSet={offset}"
        current = cat_url.rstrip("/") + f"/?offSet={offset}"
        response = self.session.post(
            GRAPHQL_URL,
            json={
                "operationName": "SearchProducts",
                "variables": {
                    "input": {
                        "searchType": "category",
                        "searchTerms": "producten",
                        "friendlyUrl": friendly,
                        "offSet": offset,
                        "currentUrl": current,
                        "previousUrl": "",
                    }
                },
                "query": _SEARCH_PRODUCTS_QUERY,
            },
            headers={
                **_GRAPHQL_HEADERS,
                "apollographql-client-name": "JUMBO_WEB-search",
                "x-source": "JUMBO_WEB-search",
            },
        )
        response.raise_for_status()
        body = response.json()
        data = body.get("data") or {}
        result = data.get("searchProducts")
        if result is None:
            self.logger.warning("searchProducts null for %s offset=%d: %s", cat_url, offset, body.get("errors"))
            return {"count": 0, "products": []}
        return result

    def _collect_products(self, result: dict, seen: set[str], products: list[ScrapedProduct], cat_id: str):
        for raw in result.get("products") or []:
            if not isinstance(raw, dict):
                continue
            product_id = raw.get("id")
            if not isinstance(product_id, str) or product_id in seen:
                continue
            seen.add(product_id)
            product = self._parse_product(raw, cat_id)
            if product:
                products.append(product)

    def _parse_product(self, raw: dict, cat_id: str) -> ScrapedProduct | None:
        product_id = raw.get("id")
        title = raw.get("title")
        if not isinstance(product_id, str) or not isinstance(title, str):
            return None

        prices = raw.get("prices") or {}
        base_price_cents = prices.get("price")
        promo_price_cents = prices.get("promoPrice")
        base_price = self._cents_to_decimal(base_price_cents) if isinstance(base_price_cents, (int, float)) else None
        has_discount = isinstance(promo_price_cents, (int, float))
        current_price = self._cents_to_decimal(promo_price_cents) if has_discount else base_price

        discount_text = None
        promotions = raw.get("promotions") or []
        if promotions and isinstance(promotions[0], dict):
            tags = promotions[0].get("tags") or []
            if tags and isinstance(tags[0], dict):
                discount_text = tags[0].get("text")

        link = raw.get("link")
        image = raw.get("image")
        return ScrapedProduct(
            external_id=product_id,
            name=title,
            base_price=base_price,
            current_price=current_price,
            has_discount=has_discount,
            discount_text=discount_text,
            image_url=image if isinstance(image, str) else None,
            website_url=BASE_URL + link if isinstance(link, str) else None,
            category_external_id=cat_id,
        )

    @staticmethod
    def _cents_to_decimal(cents: int | float) -> Decimal:
        return Decimal(cents) / Decimal(100)

    def close(self):
        self.session.close()
        self._leaf_category_urls.clear()
