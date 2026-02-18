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
        """Verify that _scrape_sub_categories finds at least 3 levels deep."""
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

    def test_product_gets_leaf_category(self):
        """Products with a subCategory name matching a 3rd-level category get the leaf ID."""
        from products.scrapers.impls.ah import BASE_URL

        # Scrape categories for just the first main category to build the name->id map.
        response = self.scraper.session.get(f"{BASE_URL}/mobile-services/v1/product-shelves/categories")
        main = response.json()[0]
        main_id = str(main["id"])
        subs = self.scraper._scrape_sub_categories(main_id)
        all_cats = [ScrapedCategory(external_id=main_id, name=main["name"])] + subs
        self.scraper._category_name_to_id = {c.name: c.external_id for c in all_cats}

        leaf_names = {c.name for c in subs if c.parent_external_id != main_id}

        # Fetch a page of products and check that at least one matches a leaf.
        response = self.scraper.session.get(
            f"{BASE_URL}/mobile-services/product/search/v2",
            params={"sortOn": "RELEVANCE", "page": 0, "size": 50},
        )
        data = response.json()
        matched = [item for item in data["products"] if item.get("subCategory") in leaf_names]
        assert len(matched) > 0, "Expected some products with subCategory matching a leaf"

        for item in matched[:5]:
            product = self.scraper._parse_product(item)
            leaf_id = self.scraper._category_name_to_id[item["subCategory"]]
            assert product.category_external_id == leaf_id

    def test_product_fields_valid(self):
        from products.scrapers.impls.ah import BASE_URL

        taxonomy_ids = self.scraper._get_taxonomy_ids()
        response = self.scraper.session.get(
            f"{BASE_URL}/mobile-services/product/search/v2",
            params={"sortOn": "RELEVANCE", "page": 0, "size": 5, "taxonomyId": taxonomy_ids[0]},
        )
        data = response.json()

        for item in data["products"][:5]:
            product = self.scraper._parse_product(item)
            assert isinstance(product, ScrapedProduct)
            assert product.external_id
            assert product.name
            assert product.current_price is not None
            assert product.current_price > 0
            assert product.website_url.startswith("https://www.ah.nl/")


class TestJumboScraperIntegration:
    @pytest.fixture(autouse=True)
    def setup_scraper(self):
        from products.scrapers.impls.jumbo import JumboScraper

        self.scraper = JumboScraper()
        yield
        self.scraper.close()

    def test_nuxt_data_parseable(self):
        from products.scrapers.impls.jumbo import PRODUCTS_PATH

        data = self.scraper._fetch_search_data(PRODUCTS_PATH)
        assert isinstance(data, list)
        assert len(data) > 0
        result = self.scraper._find_search_result(data)
        assert result is not None
        assert "products" in result
        assert "count" in result

    def test_recursive_categories_has_3_levels(self):
        """Verify recursive sub-category scraping finds leaf categories."""
        from products.scrapers.impls.jumbo import PRODUCTS_PATH

        # Get first main category tile.
        main_data = self.scraper._fetch_search_data(PRODUCTS_PATH)
        main_tiles = self.scraper._extract_category_tiles(main_data)
        tile = next(t for t in main_tiles if t.get("friendlyUrl") and "custom-category" not in t["catId"])
        main_id = tile["catId"]

        subs = self.scraper._scrape_sub_categories(main_id, PRODUCTS_PATH + tile["friendlyUrl"])

        # Should have children and grandchildren.
        assert len(subs) > 0, "Expected sub-categories"
        grandchildren = [s for s in subs if s.parent_external_id != main_id]
        assert len(grandchildren) > 0, "Expected 3rd-level categories"
        assert len(self.scraper._leaf_category_urls) > 0, "Expected leaf URLs"

    def test_leaf_products_get_correct_category(self):
        """Products from a leaf category page get that leaf's ID."""
        from products.scrapers.impls.jumbo import PRODUCTS_PATH

        # Scrape just the first main category to get leaf URLs.
        main_data = self.scraper._fetch_search_data(PRODUCTS_PATH)
        main_tiles = self.scraper._extract_category_tiles(main_data)
        tile = next(t for t in main_tiles if t.get("friendlyUrl") and "custom-category" not in t["catId"])
        self.scraper._scrape_sub_categories(tile["catId"], PRODUCTS_PATH + tile["friendlyUrl"])

        assert len(self.scraper._leaf_category_urls) > 0
        cat_id, cat_url = self.scraper._leaf_category_urls[0]

        data = self.scraper._fetch_search_data(cat_url)
        seen: set[str] = set()
        products: list[ScrapedProduct] = []
        self.scraper._collect_products(data, seen, products, category_id_override=cat_id)

        assert len(products) > 0, f"Expected products from {cat_url}"
        for p in products[:5]:
            assert p.category_external_id == cat_id

    def test_product_fields_valid(self):
        from products.scrapers.impls.jumbo import PRODUCTS_PATH

        data = self.scraper._fetch_search_data(PRODUCTS_PATH)
        seen: set[str] = set()
        products: list[ScrapedProduct] = []
        self.scraper._collect_products(data, seen, products)

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
