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


class TestLidlScraperWebsiteCompatibility:
    """Lightweight compatibility tests for the Lidl scraper.

    Each test makes at most 1-2 HTTP requests against a single known page and
    checks one structural assumption our scraper relies on.  They run in
    seconds and will start failing as soon as Lidl changes the relevant part
    of their website, giving us an early signal to update the scraper.

    These tests intentionally do NOT run a full scrape.
    """

    @pytest.fixture(autouse=True)
    def setup_scraper(self):
        from products.scrapers.impls.lidl import LidlScraper

        self.scraper = LidlScraper()
        yield
        self.scraper.close()

    # ------------------------------------------------------------------
    # Navigation structure
    # ------------------------------------------------------------------

    def test_assortment_page_has_h_category_links(self):
        """Top-level nav still exposes /h/ hierarchy links for non-food categories.

        If this fails Lidl changed their navigation structure and
        _extract_nav_categories needs to be updated.
        """
        import re

        from products.scrapers.impls.lidl import ASSORTMENT_PATH

        html = self.scraper._fetch_page(ASSORTMENT_PATH)
        h_links = re.findall(r'href="(/h/[^"]+/h\d+)"', html)
        assert len(h_links) >= 10, (
            f"Expected ≥10 /h/ links in assortment nav, got {len(h_links)}. "
            "Lidl may have changed their navigation structure."
        )

    def test_nuxt_ssr_data_contains_subcategory_triplets(self):
        """__NUXT_DATA__ script block still encodes sub-categories as triplets.

        Sub-categories like /h/krultangen/h10072341 are not linked as plain
        <a> tags — they only appear as JSON triplets in the Nuxt SSR payload.
        If this fails _extract_nuxt_categories will miss them.
        """
        import re

        html = self.scraper._fetch_page("/h/beauty-verzorging/h10067563")
        triplets = re.findall(r'"(\d{6,})","([^"]{2,80})","(/[hc]/[^/"]+/[has]\d+)"', html)
        assert len(triplets) >= 1, (
            "No sub-category triplets found in Nuxt SSR data. "
            "Lidl may have changed how sub-categories are embedded in the page."
        )

    # ------------------------------------------------------------------
    # Product data embedding
    # ------------------------------------------------------------------

    def test_category_page_embeds_products_in_data_grid_data(self):
        """Category pages still embed product JSON in data-grid-data attributes.

        If this fails _extract_grid_products will return nothing and the
        scraper will produce zero products.
        """
        html = self.scraper._fetch_page("/h/beauty-verzorging/h10067563")
        products = self.scraper._extract_grid_products(html)
        assert len(products) > 0, (
            "No data-grid-data products found on /h/beauty-verzorging/h10067563. "
            "Lidl may have changed how products are embedded in category pages."
        )

    def test_product_json_has_expected_fields(self):
        """Individual product objects still contain the keys our parser relies on.

        If productId, fullTitle, or the price structure changes the parser
        needs to be updated.
        """
        html = self.scraper._fetch_page("/h/beauty-verzorging/h10067563")
        products = self.scraper._extract_grid_products(html)
        assert len(products) > 0, "No products found, cannot check fields"
        p = products[0]
        assert "productId" in p, f"Missing 'productId'. Got keys: {list(p.keys())}"
        assert "fullTitle" in p or "canonicalUrl" in p, (
            f"Neither 'fullTitle' nor 'canonicalUrl' found. Got keys: {list(p.keys())}"
        )

    def test_priced_product_parses_correctly(self):
        """A product with a price round-trips through _parse_product without data loss."""
        from products.scrapers.impls.lidl import DEALS_PATH

        html = self.scraper._fetch_page(DEALS_PATH)
        grid_products = self.scraper._extract_grid_products(html)
        priced = [p for p in grid_products if (p.get("price") or {}).get("price")]
        assert len(priced) > 0, "No priced products on deals page — price structure may have changed"

        product = self.scraper._parse_product(priced[0])
        assert isinstance(product, ScrapedProduct)
        assert product.external_id
        assert product.name
        assert product.current_price is not None and product.current_price > 0
        assert product.website_url.startswith("https://www.lidl.nl/")

    def test_unpriced_product_is_not_dropped(self):
        """Products without a current price must still be returned by _parse_product.

        If this breaks the scraper silently drops thousands of assortment items.
        """
        html = self.scraper._fetch_page("/h/fruit-groenten/h10071012")
        grid_products = self.scraper._extract_grid_products(html)
        unpriced = [p for p in grid_products if not (p.get("price") or {}).get("price")]
        assert len(unpriced) > 0, (
            "Expected at least one product without a current price on /h/fruit-groenten. "
            "If Lidl now prices everything this assertion can be removed."
        )
        product = self.scraper._parse_product(unpriced[0])
        assert product is not None
        assert product.current_price is None

    # ------------------------------------------------------------------
    # Pagination
    # ------------------------------------------------------------------

    def test_offset_pagination_returns_different_products(self):
        """Increasing ?offset returns a different set of products.

        If this fails the pagination mechanism has changed and _scrape_category_pages
        will produce duplicates or miss products beyond the first page.
        """
        path = "/h/beauty-verzorging/h10067563"
        html0 = self.scraper._fetch_page(path)
        products0 = self.scraper._extract_grid_products(html0)
        page_size = len(products0)

        if page_size == 0:
            pytest.fail("No products on first page — cannot test pagination")

        html1 = self.scraper._fetch_page(f"{path}?offset={page_size}")
        products1 = self.scraper._extract_grid_products(html1)

        if len(products1) == 0:
            pytest.skip("Category has only one page, cannot verify pagination")

        ids0 = {str(p.get("productId")) for p in products0}
        ids1 = {str(p.get("productId")) for p in products1}
        overlap = ids0 & ids1
        assert len(overlap) < len(ids0), (
            "Offset pagination returned the same products on page 2. Lidl may have changed their pagination mechanism."
        )

    # ------------------------------------------------------------------
    # _extract_path_id (pure unit test — no HTTP)
    # ------------------------------------------------------------------

    def test_extract_path_id_all_prefixes(self):
        from products.scrapers.impls.lidl import LidlScraper

        assert LidlScraper._extract_path_id("/h/krultangen/h10072341") == "h10072341"
        assert LidlScraper._extract_path_id("/h/beauty-verzorging/h10067563") == "h10067563"
        assert LidlScraper._extract_path_id("/c/groenten-fruit/a10008017") == "a10008017"
        assert LidlScraper._extract_path_id("/c/assortiment/s10008009") == "s10008009"
        assert LidlScraper._extract_path_id("/p/some-product/p100399301") is None
        assert LidlScraper._extract_path_id("/s/nl-NL/winkel/amsterdam/") is None
