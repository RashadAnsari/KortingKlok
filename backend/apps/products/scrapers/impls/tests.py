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
            assert child.parent_external_id in all_ids, (
                f"'{child.name}' references unknown parent {child.parent_external_id}"
            )

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

    # ------------------------------------------------------------------
    # Category discovery
    # ------------------------------------------------------------------

    def test_scrape_categories_returns_results(self):
        categories = self.scraper.scrape_categories()
        assert len(categories) > 0, "Expected at least some categories"
        for cat in categories:
            assert isinstance(cat, ScrapedCategory)
            assert cat.external_id
            assert cat.name

    def test_scrape_categories_includes_h_prefix_categories(self):
        """The 71 /h/ hierarchy categories (non-food, beauty, etc.) must be found."""
        categories = self.scraper.scrape_categories()
        h_cats = [c for c in categories if c.external_id.startswith("h")]
        assert len(h_cats) >= 71, f"Expected at least 71 /h/ categories, got {len(h_cats)}"

    def test_scrape_categories_includes_known_beauty_subcategory(self):
        """Sub-categories hidden in Nuxt SSR data must be discovered.

        /h/krultangen/h10072341 (curling tongs) is only visible inside the
        Nuxt hydration data of /h/beauty-verzorging/h10067563 — it does NOT
        appear as a plain anchor tag anywhere in the top-level navigation.
        """
        categories = self.scraper.scrape_categories()
        ids = {c.external_id for c in categories}
        assert "h10072341" in ids, "h10072341 (krultangen) not found — Nuxt sub-category extraction is broken"

    def test_category_ids_are_unique(self):
        categories = self.scraper.scrape_categories()
        ids = [c.external_id for c in categories]
        assert len(ids) == len(set(ids)), "Duplicate category external_ids detected"

    def test_category_names_are_non_empty(self):
        categories = self.scraper.scrape_categories()
        for cat in categories:
            assert cat.name.strip(), f"Category {cat.external_id} has an empty name"

    # ------------------------------------------------------------------
    # Product parsing
    # ------------------------------------------------------------------

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

    def test_h_category_page_has_products(self):
        """An /h/ category page must yield data-grid-data products."""
        # Use the beauty sub-category from the user's reported missing product.
        page_html = self.scraper._fetch_page("/h/krultangen/h10072341")
        products = self.scraper._extract_grid_products(page_html)
        assert len(products) > 0, "Expected products on /h/krultangen/h10072341"
        # The specific product reported by the user must be present.
        pids = {str(p.get("productId")) for p in products}
        assert "100399301" in pids, "Product p100399301 (Cien fohnborstel) not found"

    def test_product_without_price_is_not_dropped(self):
        """Products in the assortment that lack a current price must still be returned."""
        # Fetch a known /h/ page that contains unpriced items.
        page_html = self.scraper._fetch_page("/h/fruit-groenten/h10071012")
        grid_products = self.scraper._extract_grid_products(page_html)
        unpriced = [p for p in grid_products if not (p.get("price") or {}).get("price")]
        assert len(unpriced) > 0, "Expected at least one product without a current price"
        for data in unpriced[:3]:
            product = self.scraper._parse_product(data)
            assert product is not None
            assert product.base_price is None
            assert product.current_price is None

    def test_product_fields_valid(self):
        """Products parsed from a live /h/ page have all required fields."""
        self.scraper.scrape_categories()
        page_html = self.scraper._fetch_page("/h/beauty-verzorging/h10067563")
        grid_products = self.scraper._extract_grid_products(page_html)
        assert len(grid_products) > 0

        for data in grid_products[:5]:
            product = self.scraper._parse_product(data, "h10067563")
            assert isinstance(product, ScrapedProduct)
            assert product.external_id
            assert product.name
            assert product.website_url and product.website_url.startswith("https://www.lidl.nl/")
            assert product.category_external_id == "h10067563"

    # ------------------------------------------------------------------
    # Pagination
    # ------------------------------------------------------------------

    def test_pagination_fetches_beyond_first_48(self):
        """Pagination must advance past offset=0 for large categories.

        /h/beauty-verzorging has more than 48 products across multiple pages.
        The adaptive step size (derived from the first page's count) must
        correctly step to offset=48, not get stuck at offset=24.
        """
        seen: dict = {}
        self.scraper._scrape_category_pages(
            "h10067563",
            "/h/beauty-verzorging/h10067563",
            seen,
        )
        assert len(seen) > 48, f"Expected more than 48 products from beauty category, got {len(seen)}"

    # ------------------------------------------------------------------
    # _extract_path_id
    # ------------------------------------------------------------------

    def test_extract_path_id_handles_h_prefix(self):
        from products.scrapers.impls.lidl import LidlScraper

        assert LidlScraper._extract_path_id("/h/krultangen/h10072341") == "h10072341"
        assert LidlScraper._extract_path_id("/h/beauty-verzorging/h10067563") == "h10067563"

    def test_extract_path_id_handles_a_and_s_prefix(self):
        from products.scrapers.impls.lidl import LidlScraper

        assert LidlScraper._extract_path_id("/c/groenten-fruit/a10008017") == "a10008017"
        assert LidlScraper._extract_path_id("/c/assortiment/s10008009") == "s10008009"

    def test_extract_path_id_returns_none_for_unknown(self):
        from products.scrapers.impls.lidl import LidlScraper

        assert LidlScraper._extract_path_id("/p/some-product/p100399301") is None
        assert LidlScraper._extract_path_id("/s/nl-NL/winkel/amsterdam/") is None
