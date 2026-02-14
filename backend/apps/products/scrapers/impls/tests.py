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
