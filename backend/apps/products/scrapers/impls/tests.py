import pytest

from products.scrapers.dtos import ScrapedProduct


class TestAlbertHeijnScraperWebsiteCompatibility:
    @pytest.fixture(autouse=True)
    def setup_scraper(self):
        from products.scrapers.impls.ah import AlbertHeijnScraper

        self.scraper = AlbertHeijnScraper()
        yield
        self.scraper.close()

    def test_anonymous_auth_returns_bearer_token(self):
        assert (
            "Authorization" in self.scraper.session.headers
        ), "No Authorization header set after init — auth endpoint may have changed"
        assert self.scraper.session.headers["Authorization"].startswith(
            "Bearer "
        ), "Authorization header is not a Bearer token — token scheme may have changed"

    def test_categories_endpoint_returns_id_and_name(self):
        from products.scrapers.impls.ah import BASE_URL

        response = self.scraper.session.get(f"{BASE_URL}/mobile-services/v1/product-shelves/categories")
        response.raise_for_status()
        categories = response.json()
        assert len(categories) > 0, "Categories endpoint returned an empty list"
        first = categories[0]
        assert "id" in first, f"Missing 'id' in category object. Got keys: {list(first.keys())}"
        assert "name" in first, f"Missing 'name' in category object. Got keys: {list(first.keys())}"

    def test_subcategories_endpoint_returns_children_key(self):
        from products.scrapers.impls.ah import BASE_URL

        cats = self.scraper.session.get(f"{BASE_URL}/mobile-services/v1/product-shelves/categories").json()
        main_id = str(cats[0]["id"])
        response = self.scraper.session.get(
            f"{BASE_URL}/mobile-services/v1/product-shelves/categories/{main_id}/sub-categories"
        )
        response.raise_for_status()
        data = response.json()
        assert "children" in data, (
            f"Missing 'children' key in sub-categories response. Got keys: {list(data.keys())}. "
            "AH may have changed the sub-categories endpoint structure."
        )

    def test_product_search_accepts_taxonomy_id_and_returns_products(self):
        from products.scrapers.impls.ah import BASE_URL

        # Walk down to the first leaf without a full recursive scrape.
        cats = self.scraper.session.get(f"{BASE_URL}/mobile-services/v1/product-shelves/categories").json()
        main_id = str(cats[0]["id"])
        subs = self.scraper.session.get(
            f"{BASE_URL}/mobile-services/v1/product-shelves/categories/{main_id}/sub-categories"
        ).json()
        leaf_id = str(subs["children"][0]["id"]) if subs.get("children") else main_id

        response = self.scraper.session.get(
            f"{BASE_URL}/mobile-services/product/search/v2",
            params={"sortOn": "RELEVANCE", "page": 0, "size": 3, "taxonomyId": leaf_id},
        )
        response.raise_for_status()
        data = response.json()

        assert "products" in data, f"Missing 'products' key in search response. Got: {list(data.keys())}"
        assert "page" in data, f"Missing 'page' key in search response. Got: {list(data.keys())}"
        assert "totalPages" in data["page"], f"Missing 'totalPages' in page object. Got: {list(data['page'].keys())}"
        assert len(data["products"]) > 0, "Product search returned zero products for a leaf category"

    def test_product_json_has_expected_fields(self):
        from products.scrapers.impls.ah import BASE_URL

        cats = self.scraper.session.get(f"{BASE_URL}/mobile-services/v1/product-shelves/categories").json()
        main_id = str(cats[0]["id"])
        subs = self.scraper.session.get(
            f"{BASE_URL}/mobile-services/v1/product-shelves/categories/{main_id}/sub-categories"
        ).json()
        leaf_id = str(subs["children"][0]["id"]) if subs.get("children") else main_id

        data = self.scraper.session.get(
            f"{BASE_URL}/mobile-services/product/search/v2",
            params={"sortOn": "RELEVANCE", "page": 0, "size": 3, "taxonomyId": leaf_id},
        ).json()
        item = data["products"][0]

        assert "webshopId" in item, f"Missing 'webshopId'. Got keys: {list(item.keys())}"
        assert "title" in item, f"Missing 'title'. Got keys: {list(item.keys())}"

        product = self.scraper._parse_product(item, leaf_id)
        assert isinstance(product, ScrapedProduct)
        assert product.external_id
        assert product.name
        assert product.website_url.startswith("https://www.ah.nl/")


class TestJumboScraperWebsiteCompatibility:
    @pytest.fixture(autouse=True)
    def setup_scraper(self):
        from products.scrapers.impls.jumbo import JumboScraper

        self.scraper = JumboScraper()
        yield
        self.scraper.close()

    def test_categories_tree_query_returns_data(self):
        from products.scrapers.impls.jumbo import _CATEGORIES_TREE_QUERY, _GRAPHQL_HEADERS, GRAPHQL_URL

        response = self.scraper.session.post(
            GRAPHQL_URL,
            json={"operationName": "CategoriesTree", "variables": {}, "query": _CATEGORIES_TREE_QUERY},
            headers={**_GRAPHQL_HEADERS, "apollographql-client-name": "JUMBO_WEB-cms", "x-source": "JUMBO_WEB-cms"},
        )
        response.raise_for_status()
        data = response.json()

        assert "data" in data, f"GraphQL response missing 'data'. Got keys: {list(data.keys())}"
        assert "categoriesTree" in data["data"], (
            f"Missing 'categoriesTree' in data. Got keys: {list(data['data'].keys())}. "
            "Jumbo may have renamed the CategoriesTree query or its return type."
        )
        assert len(data["data"]["categoriesTree"]) > 0, "CategoriesTree returned an empty list"

    def test_category_objects_have_title_and_link(self):
        from products.scrapers.impls.jumbo import _CATEGORIES_TREE_QUERY, _GRAPHQL_HEADERS, GRAPHQL_URL

        cats = self.scraper.session.post(
            GRAPHQL_URL,
            json={"operationName": "CategoriesTree", "variables": {}, "query": _CATEGORIES_TREE_QUERY},
            headers={**_GRAPHQL_HEADERS, "apollographql-client-name": "JUMBO_WEB-cms", "x-source": "JUMBO_WEB-cms"},
        ).json()["data"]["categoriesTree"]

        first = cats[0]
        assert "title" in first, f"Missing 'title' in category. Got keys: {list(first.keys())}"
        assert "link" in first, f"Missing 'link' in category. Got keys: {list(first.keys())}"
        assert first["link"].startswith("/producten/"), (
            f"Category link '{first['link']}' does not start with '/producten/'. "
            "The ID derivation in scrape_categories will produce wrong IDs."
        )

    def test_categories_have_subpages(self):
        from products.scrapers.impls.jumbo import _CATEGORIES_TREE_QUERY, _GRAPHQL_HEADERS, GRAPHQL_URL

        cats = self.scraper.session.post(
            GRAPHQL_URL,
            json={"operationName": "CategoriesTree", "variables": {}, "query": _CATEGORIES_TREE_QUERY},
            headers={**_GRAPHQL_HEADERS, "apollographql-client-name": "JUMBO_WEB-cms", "x-source": "JUMBO_WEB-cms"},
        ).json()["data"]["categoriesTree"]

        cats_with_subs = [c for c in cats if c.get("subpages")]
        assert len(cats_with_subs) > 0, (
            "No main category has 'subpages'. "
            "Jumbo may have renamed the sub-categories field or changed the query depth."
        )

    def test_search_products_query_returns_count_and_products(self):
        from products.scrapers.impls.jumbo import _CATEGORIES_TREE_QUERY, _GRAPHQL_HEADERS, GRAPHQL_URL

        cats = self.scraper.session.post(
            GRAPHQL_URL,
            json={"operationName": "CategoriesTree", "variables": {}, "query": _CATEGORIES_TREE_QUERY},
            headers={**_GRAPHQL_HEADERS, "apollographql-client-name": "JUMBO_WEB-cms", "x-source": "JUMBO_WEB-cms"},
        ).json()["data"]["categoriesTree"]

        # Find the first sub-category URL without a full scrape.
        leaf_url = next(
            (sub["link"] for cat in cats for sub in (cat.get("subpages") or []) if sub.get("link")),
            None,
        )
        assert leaf_url is not None, "No sub-category link found to test SearchProducts against"

        result = self.scraper._fetch_products_page(leaf_url, 0)
        assert "count" in result, f"Missing 'count' in SearchProducts response. Got keys: {list(result.keys())}"
        assert "products" in result, f"Missing 'products' in SearchProducts response. Got keys: {list(result.keys())}"
        assert result["count"] > 0, "SearchProducts returned count=0 for a leaf category"
        assert len(result["products"]) > 0, "SearchProducts returned empty products list"

    def test_product_json_has_expected_fields(self):
        from products.scrapers.impls.jumbo import _CATEGORIES_TREE_QUERY, _GRAPHQL_HEADERS, GRAPHQL_URL

        cats = self.scraper.session.post(
            GRAPHQL_URL,
            json={"operationName": "CategoriesTree", "variables": {}, "query": _CATEGORIES_TREE_QUERY},
            headers={**_GRAPHQL_HEADERS, "apollographql-client-name": "JUMBO_WEB-cms", "x-source": "JUMBO_WEB-cms"},
        ).json()["data"]["categoriesTree"]

        leaf_url = next(
            (sub["link"] for cat in cats for sub in (cat.get("subpages") or []) if sub.get("link")),
            None,
        )
        assert leaf_url is not None, "No sub-category link found"
        leaf_id = leaf_url.removeprefix("/producten/").strip("/")

        result = self.scraper._fetch_products_page(leaf_url, 0)
        item = result["products"][0]

        assert "id" in item, f"Missing 'id' (sku) in product. Got keys: {list(item.keys())}"
        assert "title" in item, f"Missing 'title' in product. Got keys: {list(item.keys())}"
        assert "prices" in item, f"Missing 'prices' in product. Got keys: {list(item.keys())}"
        assert "price" in (item.get("prices") or {}), f"Missing 'price' inside 'prices'. Got: {item.get('prices')}"

        product = self.scraper._parse_product(item, leaf_id)
        assert isinstance(product, ScrapedProduct)
        assert product.external_id
        assert product.name
        assert product.website_url and product.website_url.startswith("https://www.jumbo.com/")


class TestLidlScraperWebsiteCompatibility:
    @pytest.fixture(autouse=True)
    def setup_scraper(self):
        from products.scrapers.impls.lidl import LidlScraper

        self.scraper = LidlScraper()
        yield
        self.scraper.close()

    def test_assortment_page_has_h_category_links(self):
        from products.scrapers.impls.lidl import ASSORTMENT_PATH

        html = self.scraper._fetch_page(ASSORTMENT_PATH)
        cats = self.scraper._extract_nav_categories(html)
        h_cats = [c for c in cats if c.external_id.startswith("h")]
        assert len(h_cats) >= 10, (
            f"Expected ≥10 /h/ categories in assortment nav, got {len(h_cats)}. "
            "Lidl may have changed their navigation structure."
        )

    def test_nuxt_ssr_data_contains_subcategories(self):
        from products.scrapers.impls.lidl import (
            _RE_NUXT_CATEGORY,
            _RE_NUXT_SCRIPT,
            _unescape_nuxt_slashes,
        )

        html = self.scraper._fetch_page("/h/beauty-verzorging/h10067563")
        nuxt_match = _RE_NUXT_SCRIPT.search(html)
        assert nuxt_match is not None, (
            "No __NUXT_DATA__ script block found on beauty category page. "
            "Lidl may have removed or renamed the Nuxt SSR hydration script."
        )
        matches = _RE_NUXT_CATEGORY.findall(_unescape_nuxt_slashes(nuxt_match.group(1)))
        assert len(matches) >= 1, (
            "No sub-categories found inside __NUXT_DATA__ block. "
            "Lidl may have changed how sub-categories are embedded in the SSR data."
        )

    def test_nuxt_subcategory_extraction_returns_children(self):
        html = self.scraper._fetch_page("/h/beauty-verzorging/h10067563")
        subs = self.scraper._extract_nuxt_categories(
            html,
            parent_id="h10067563",
            seen_ids={"h10067563"},
        )
        assert len(subs) >= 1, (
            "No sub-categories extracted for /h/beauty-verzorging/h10067563. "
            "The SSR pattern matched but produced no usable categories."
        )
        assert all(c.parent_external_id == "h10067563" for c in subs)
        assert all(c.name for c in subs)
        # The breadcrumb ancestor shares the pattern and must not come back
        # as a child of the page it sits above.
        assert not [c for c in subs if c.external_id.startswith("s")]

    def test_category_page_embeds_products_in_data_grid_data(self):
        html = self.scraper._fetch_page("/h/beauty-verzorging/h10067563")
        products = self.scraper._extract_grid_products(html)
        assert len(products) > 0, (
            "No data-grid-data products found on /h/beauty-verzorging/h10067563. "
            "Lidl may have changed how products are embedded in category pages."
        )

    def test_product_json_has_expected_fields(self):
        html = self.scraper._fetch_page("/h/beauty-verzorging/h10067563")
        products = self.scraper._extract_grid_products(html)
        assert len(products) > 0, "No products found, cannot check fields"
        p = products[0]
        assert "productId" in p, f"Missing 'productId'. Got keys: {list(p.keys())}"
        assert "title" in p, f"Missing 'title'. Got keys: {list(p.keys())}"
        assert "canonicalPath" in p, f"Missing 'canonicalPath'. Got keys: {list(p.keys())}"

    def test_priced_product_parses_correctly(self):
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

    def test_offset_pagination_returns_different_products(self):
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
        assert len(overlap) < len(
            ids0
        ), "Offset pagination returned the same products on page 2. Lidl may have changed their pagination mechanism."

    def test_extract_path_id_all_prefixes(self):
        from products.scrapers.impls.lidl import LidlScraper

        assert LidlScraper._extract_path_id("/h/krultangen/h10072341") == "h10072341"
        assert LidlScraper._extract_path_id("/h/beauty-verzorging/h10067563") == "h10067563"
        assert LidlScraper._extract_path_id("/c/groenten-fruit/a10008017") == "a10008017"
        assert LidlScraper._extract_path_id("/c/assortiment/s10008009") == "s10008009"
        assert LidlScraper._extract_path_id("/p/some-product/p100399301") is None
        assert LidlScraper._extract_path_id("/s/nl-NL/winkel/amsterdam/") is None
