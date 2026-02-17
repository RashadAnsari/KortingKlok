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

    def test_scrape_categories_returns_results(self):
        categories = self.scraper.scrape_categories()
        assert len(categories) > 0
        for cat in categories[:5]:
            assert isinstance(cat, ScrapedCategory)
            assert cat.external_id
            assert cat.name

    def test_fetch_single_product_page(self):
        from products.scrapers.impls.ah import BASE_URL, PAGE_SIZE

        taxonomy_ids = self.scraper._get_taxonomy_ids()
        assert len(taxonomy_ids) > 0

        response = self.scraper.session.get(
            f"{BASE_URL}/mobile-services/product/search/v2",
            params={"sortOn": "RELEVANCE", "page": 0, "size": PAGE_SIZE, "taxonomyId": taxonomy_ids[0]},
        )
        response.raise_for_status()
        data = response.json()

        assert "products" in data
        assert len(data["products"]) > 0
        assert "page" in data
        assert "totalPages" in data["page"]

    def test_product_fields_valid(self):
        from products.scrapers.impls.ah import BASE_URL

        taxonomy_ids = self.scraper._get_taxonomy_ids()
        response = self.scraper.session.get(
            f"{BASE_URL}/mobile-services/product/search/v2",
            params={"sortOn": "RELEVANCE", "page": 0, "size": 10, "taxonomyId": taxonomy_ids[0]},
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

    def test_some_products_have_discount(self):
        from products.scrapers.impls.ah import BASE_URL

        response = self.scraper.session.get(
            f"{BASE_URL}/mobile-services/product/search/v2",
            params={"sortOn": "RELEVANCE", "page": 0, "size": 1000, "taxonomyId": self.scraper._get_taxonomy_ids()[0]},
        )
        data = response.json()
        products = [self.scraper._parse_product(item) for item in data["products"]]
        discounted = [p for p in products if p.has_discount]
        assert len(discounted) > 0, "Expected at least some discounted products"
        for p in discounted[:3]:
            assert p.base_price >= p.current_price

    def test_categories_have_parent_child_hierarchy(self):
        categories = self.scraper.scrape_categories()
        parents = [c for c in categories if c.parent_external_id is None]
        children = [c for c in categories if c.parent_external_id is not None]
        assert len(parents) > 0, "Expected main categories"
        assert len(children) > 0, "Expected sub-categories"
        # Every child must reference an existing parent.
        parent_ids = {c.external_id for c in parents}
        for child in children:
            assert (
                child.parent_external_id in parent_ids
            ), f"Sub-category '{child.name}' references unknown parent {child.parent_external_id}"

    def test_products_use_sub_category_when_possible(self):
        """Products should be matched to sub-categories when the name allows it.

        AH product subCategory values (e.g. "Komkommer") are more specific than
        category API names (e.g. "Komkommer, tomaten, avocado"). The substring
        matching works for many but not all products. We verify that it matches
        at least some products across multiple taxonomies.
        """
        from products.scrapers.impls.ah import BASE_URL

        categories = self.scraper.scrape_categories()
        sub_cat_ids = {c.external_id for c in categories if c.parent_external_id is not None}
        assert len(sub_cat_ids) > 0

        # Sample products across several taxonomies for a representative test.
        taxonomy_ids = self.scraper._get_taxonomy_ids()
        all_products = []
        for tax_id in taxonomy_ids[:5]:
            response = self.scraper.session.get(
                f"{BASE_URL}/mobile-services/product/search/v2",
                params={"sortOn": "RELEVANCE", "page": 0, "size": 30, "taxonomyId": tax_id},
            )
            data = response.json()
            all_products.extend(self.scraper._parse_product(item) for item in data["products"])

        with_sub = [p for p in all_products if p.category_external_id in sub_cat_ids]
        assert len(with_sub) > 0, f"Expected at least some products to match a sub-category, got 0/{len(all_products)}"


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

    def test_scrape_categories_returns_results(self):
        categories = self.scraper.scrape_categories()
        assert len(categories) > 0
        for cat in categories[:5]:
            assert isinstance(cat, ScrapedCategory)
            assert cat.external_id
            assert cat.name

    def test_fetch_single_page_products(self):
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

    def test_total_count_reasonable(self):
        from products.scrapers.impls.jumbo import PRODUCTS_PATH

        data = self.scraper._fetch_search_data(PRODUCTS_PATH)
        count = self.scraper._extract_count(data)
        assert count > 5000, f"Expected >5000 total products, got {count}"

    def test_categories_have_parent_child_hierarchy(self):
        categories = self.scraper.scrape_categories()
        parents = [c for c in categories if c.parent_external_id is None]
        children = [c for c in categories if c.parent_external_id is not None]
        assert len(parents) > 0, "Expected main categories"
        assert len(children) > 0, "Expected sub-categories"
        parent_ids = {c.external_id for c in parents}
        for child in children:
            assert (
                child.parent_external_id in parent_ids
            ), f"Sub-category '{child.name}' references unknown parent {child.parent_external_id}"

    def test_scrape_categories_populates_sub_category_urls(self):
        self.scraper.scrape_categories()
        assert len(self.scraper._sub_category_urls) > 0, "Expected sub-category URLs to be populated"
        for cat_id, url in self.scraper._sub_category_urls[:3]:
            assert cat_id
            assert url.startswith("/producten/")

    def test_products_from_sub_category_get_correct_id(self):
        """Products scraped from a sub-category page should get that sub-category's ID."""
        self.scraper.scrape_categories()
        assert len(self.scraper._sub_category_urls) > 0

        cat_id, cat_url = self.scraper._sub_category_urls[0]
        data = self.scraper._fetch_search_data(cat_url)
        seen: set[str] = set()
        products: list[ScrapedProduct] = []
        self.scraper._collect_products(data, seen, products, category_id_override=cat_id)

        assert len(products) > 0, f"Expected products from sub-category page {cat_url}"
        for p in products:
            assert (
                p.category_external_id == cat_id
            ), f"Product '{p.name}' has category_external_id={p.category_external_id}, expected {cat_id}"


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

    def test_assortment_page_loads(self):
        from products.scrapers.impls.lidl import ASSORTMENT_PATH

        page_html = self.scraper._fetch_page(ASSORTMENT_PATH)
        assert len(page_html) > 1000

    def test_deals_page_loads(self):
        from products.scrapers.impls.lidl import DEALS_PATH

        page_html = self.scraper._fetch_page(DEALS_PATH)
        assert len(page_html) > 1000

    def test_grid_data_parseable(self):
        from products.scrapers.impls.lidl import DEALS_PATH

        page_html = self.scraper._fetch_page(DEALS_PATH)
        products = self.scraper._extract_grid_products(page_html)
        for p in products:
            assert "productId" in p
            assert "title" in p

    def test_parsed_products_have_valid_fields(self):
        from products.scrapers.impls.lidl import DEALS_PATH

        page_html = self.scraper._fetch_page(DEALS_PATH)
        grid_products = self.scraper._extract_grid_products(page_html)

        for data in grid_products:
            product = self.scraper._parse_product(data)
            assert product is not None
            assert isinstance(product, ScrapedProduct)
            assert product.external_id
            assert product.name
            assert product.website_url.startswith("https://www.lidl.nl/")
