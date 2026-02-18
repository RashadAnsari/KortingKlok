import pytest

from products.scrapers.dtos import ScrapedCategory, ScrapedProduct


class TestAlbertHeijnScraperIntegration:
    @pytest.fixture(autouse=True)
    def setup_scraper(self):
        from products.scrapers.impls.ah import AlbertHeijnScraper

        self.scraper = AlbertHeijnScraper()
        yield
        self.scraper.close()

    def test_obtains_auth_token(self):
        assert "Authorization" in self.scraper.session.headers
        assert self.scraper.session.headers["Authorization"].startswith("Bearer ")

    def test_recursive_categories_has_3_levels(self):
        """Verify that _scrape_sub_categories finds at least 3 levels deep and populates leaf IDs."""
        from products.scrapers.impls.ah import BASE_URL

        # Get first main category.
        response = self.scraper.session.get(f"{BASE_URL}/mobile-services/v1/product-shelves/categories")
        main_categories = response.json()
        main_id = str(main_categories[0]["id"])

        # Recursively scrape just one main category.
        subs = self.scraper._scrape_sub_categories(main_id)
        assert len(subs) > 0, "Expected sub-categories"

        # Should have grandchildren (parent_external_id != main_id).
        grandchildren = [s for s in subs if s.parent_external_id != main_id]
        assert len(grandchildren) > 0, "Expected 3rd-level categories"

        # Leaf category IDs should be populated and usable as taxonomy filters.
        assert len(self.scraper._leaf_category_ids) > 0, "Expected leaf category IDs"
        response = self.scraper.session.get(
            f"{BASE_URL}/mobile-services/product/search/v2",
            params={"sortOn": "RELEVANCE", "page": 0, "size": 1, "taxonomyId": self.scraper._leaf_category_ids[0]},
        )
        data = response.json()
        assert data["page"]["totalElements"] > 0, "Leaf category should return products via taxonomyId"

    def test_product_fields_valid(self):
        from products.scrapers.impls.ah import BASE_URL

        self.scraper.scrape_categories()
        leaf_id = self.scraper._leaf_category_ids[0]

        response = self.scraper.session.get(
            f"{BASE_URL}/mobile-services/product/search/v2",
            params={"sortOn": "RELEVANCE", "page": 0, "size": 5, "taxonomyId": leaf_id},
        )
        data = response.json()

        for item in data["products"][:5]:
            product = self.scraper._parse_product(item, leaf_id)
            assert isinstance(product, ScrapedProduct)
            assert product.external_id
            assert product.name
            assert product.current_price is not None
            assert product.current_price > 0
            assert product.website_url.startswith("https://www.ah.nl/")
            assert product.category_external_id == leaf_id


class TestJumboScraperIntegration:
    @pytest.fixture(autouse=True)
    def setup_scraper(self):
        from products.scrapers.impls.jumbo import JumboScraper

        self.scraper = JumboScraper()
        yield
        self.scraper.close()

    def test_graphql_products_parseable(self):
        """SearchProducts GraphQL returns parseable data for the first leaf category."""
        self.scraper.scrape_categories()
        assert len(self.scraper._leaf_category_urls) > 0
        _, cat_url = self.scraper._leaf_category_urls[0]
        result = self.scraper._fetch_products_page(cat_url, 0)
        assert isinstance(result, dict)
        assert "products" in result
        assert "count" in result

    def test_graphql_categories(self):
        """scrape_categories() uses a single GraphQL call and returns a 2-level hierarchy."""
        categories = self.scraper.scrape_categories()

        parents = [c for c in categories if c.parent_external_id is None]
        children = [c for c in categories if c.parent_external_id is not None]
        all_ids = {c.external_id for c in categories}

        assert len(parents) > 0, "Expected main categories"
        assert len(children) > 0, "Expected sub/leaf categories"
        assert len(self.scraper._leaf_category_urls) > 0, "Expected leaf URLs"

        for child in children:
            assert (
                child.parent_external_id in all_ids
            ), f"'{child.name}' references unknown parent {child.parent_external_id}"

        # IDs should be slug-based paths, not numeric.
        for cat in categories[:5]:
            assert "/" in cat.external_id or "-" in cat.external_id, f"Expected slug-based ID, got {cat.external_id}"

    def test_leaf_products_get_correct_category(self):
        """Products from a leaf category page get that leaf's ID."""
        self.scraper.scrape_categories()

        assert len(self.scraper._leaf_category_urls) > 0
        cat_id, cat_url = self.scraper._leaf_category_urls[0]

        result = self.scraper._fetch_products_page(cat_url, 0)
        seen: set[str] = set()
        products: list[ScrapedProduct] = []
        self.scraper._collect_products(result, seen, products, cat_id)

        assert len(products) > 0, f"Expected products from {cat_url}"
        for p in products[:5]:
            assert p.category_external_id == cat_id

    def test_product_fields_valid(self):
        self.scraper.scrape_categories()
        _, cat_url = self.scraper._leaf_category_urls[0]
        result = self.scraper._fetch_products_page(cat_url, 0)
        seen: set[str] = set()
        products: list[ScrapedProduct] = []
        self.scraper._collect_products(result, seen, products, "test-cat")

        assert len(products) > 0
        for p in products[:5]:
            assert isinstance(p, ScrapedProduct)
            assert p.external_id
            assert p.name
            assert p.current_price is not None
            assert p.current_price > 0
            assert p.website_url.startswith("https://www.jumbo.com/")


class TestLidlScraperIntegration:
    @pytest.fixture(autouse=True)
    def setup_scraper(self):
        from products.scrapers.impls.lidl import LidlScraper

        self.scraper = LidlScraper()
        yield
        self.scraper.close()

    def test_scrape_categories_returns_results(self):
        categories = self.scraper.scrape_categories()
        assert len(categories) > 0, "Expected at least some categories"
        for cat in categories:
            assert isinstance(cat, ScrapedCategory)
            assert cat.external_id
            assert cat.name

    def test_deals_have_products_with_prices(self):
        from products.scrapers.impls.lidl import DEALS_PATH

        page_html = self.scraper._fetch_page(DEALS_PATH)
        grid_products = self.scraper._extract_grid_products(page_html)

        for data in grid_products[:5]:
            product = self.scraper._parse_product(data)
            assert product is not None
            assert isinstance(product, ScrapedProduct)
            assert product.external_id
            assert product.name
            assert product.website_url.startswith("https://www.lidl.nl/")
