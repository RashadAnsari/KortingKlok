import pytest
from rest_framework.test import APIClient
from users.auths import InternalUser

from products.models import Category, Product, Supermarket, UserTrackedProduct

DEALS_URL = "/v1/products/deals"
SEARCH_URL = "/v1/products/search"
CATEGORIES_URL = "/v1/products/categories"
SUPERMARKETS_URL = "/v1/products/supermarkets"


@pytest.fixture
def user():
    return InternalUser(uid="user123")


@pytest.fixture
def api_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def supermarket():
    return Supermarket.objects.create(name="Albert Heijn", slug="ah")


@pytest.fixture
def supermarket2():
    return Supermarket.objects.create(name="Jumbo", slug="jumbo")


@pytest.fixture
def category(supermarket):
    return Category.objects.create(name="Zuivel", supermarket=supermarket)


@pytest.fixture
def product(supermarket, category):
    return Product.objects.create(
        name="Kaas 48+",
        external_id="ext-1",
        supermarket=supermarket,
        category=category,
        current_price="2.99",
        base_price="3.99",
        has_discount=True,
    )


@pytest.mark.django_db
class TestSupermarketList:
    def test_returns_all_supermarkets(self, api_client, supermarket, supermarket2):
        response = api_client.get(SUPERMARKETS_URL)
        assert response.status_code == 200
        assert len(response.data) == 2

    def test_returns_expected_fields(self, api_client, supermarket):
        response = api_client.get(SUPERMARKETS_URL)
        item = response.data[0]
        assert "id" in item
        assert "name" in item
        assert "slug" in item
        assert "logo_url" in item
        assert "website_url" in item

    def test_ordered_by_name(self, api_client, supermarket, supermarket2):
        response = api_client.get(SUPERMARKETS_URL)
        names = [s["name"] for s in response.data]
        assert names == sorted(names)

    def test_requires_authentication(self):
        response = APIClient().get(SUPERMARKETS_URL)
        assert response.status_code == 401


@pytest.mark.django_db
class TestCategoryList:
    def test_returns_all_categories_without_filter(self, api_client, category):
        response = api_client.get(CATEGORIES_URL)
        assert response.status_code == 200
        assert len(response.data) == 1

    def test_filters_by_supermarket(self, api_client, supermarket, supermarket2, category):
        cat2 = Category.objects.create(name="Brood", supermarket=supermarket2)
        response = api_client.get(CATEGORIES_URL, {"supermarket": supermarket.id})
        assert response.status_code == 200
        ids = [c["id"] for c in response.data]
        assert category.id in ids
        assert cat2.id not in ids

    def test_returns_expected_fields(self, api_client, category):
        response = api_client.get(CATEGORIES_URL)
        item = response.data[0]
        assert "id" in item
        assert "name" in item
        assert "parent" in item

    def test_parent_is_null_for_root_category(self, api_client, category):
        response = api_client.get(CATEGORIES_URL)
        assert response.data[0]["parent"] is None

    def test_parent_is_set_for_child_category(self, api_client, supermarket, category):
        child = Category.objects.create(name="Halfvolle melk", supermarket=supermarket, parent=category)
        response = api_client.get(CATEGORIES_URL, {"supermarket": supermarket.id, "parent": category.id})
        assert len(response.data) == 1
        assert response.data[0]["id"] == child.id
        assert response.data[0]["parent"] == category.id

    def test_filters_by_parent(self, api_client, supermarket, category):
        child1 = Category.objects.create(name="Halfvolle melk", supermarket=supermarket, parent=category)
        child2 = Category.objects.create(name="Volle melk", supermarket=supermarket, parent=category)
        Category.objects.create(name="Brood", supermarket=supermarket)  # root, excluded
        response = api_client.get(CATEGORIES_URL, {"parent": category.id})
        assert response.status_code == 200
        ids = [c["id"] for c in response.data]
        assert child1.id in ids
        assert child2.id in ids
        assert category.id not in ids

    def test_default_returns_root_categories(self, api_client, supermarket, category):
        child = Category.objects.create(name="Halfvolle melk", supermarket=supermarket, parent=category)
        response = api_client.get(CATEGORIES_URL)
        ids = [c["id"] for c in response.data]
        assert category.id in ids
        assert child.id not in ids

    def test_requires_authentication(self):
        response = APIClient().get(CATEGORIES_URL)
        assert response.status_code == 401


@pytest.mark.django_db
class TestProductSearch:
    def test_returns_available_products(self, api_client, product):
        response = api_client.get(SEARCH_URL)
        assert response.status_code == 200
        assert response.data["count"] == 1

    def test_excludes_unavailable_products(self, api_client, supermarket):
        Product.objects.create(
            name="Unavailable",
            external_id="ext-unavail",
            supermarket=supermarket,
            is_available=False,
        )
        response = api_client.get(SEARCH_URL)
        assert response.data["count"] == 0

    def test_filters_by_query(self, api_client, product, supermarket):
        Product.objects.create(name="Yoghurt", external_id="ext-2", supermarket=supermarket, is_available=True)
        response = api_client.get(SEARCH_URL, {"q": "kaas"})
        assert response.data["count"] == 1
        assert response.data["results"][0]["name"] == "Kaas 48+"

    def test_query_is_case_insensitive(self, api_client, product):
        response = api_client.get(SEARCH_URL, {"q": "KAAS"})
        assert response.data["count"] == 1

    def test_filters_by_supermarket(self, api_client, product, supermarket2):
        Product.objects.create(name="Kaas jumbo", external_id="ext-j1", supermarket=supermarket2, is_available=True)
        response = api_client.get(SEARCH_URL, {"supermarket": supermarket2.id})
        assert response.data["count"] == 1
        assert response.data["results"][0]["name"] == "Kaas jumbo"

    def test_filters_by_category(self, api_client, product, supermarket, category):
        cat2 = Category.objects.create(name="Brood", supermarket=supermarket)
        Product.objects.create(
            name="Brood", external_id="ext-b1", supermarket=supermarket, category=cat2, is_available=True
        )
        response = api_client.get(SEARCH_URL, {"category": category.id})
        assert response.data["count"] == 1
        assert response.data["results"][0]["name"] == "Kaas 48+"

    def test_discounted_products_appear_first(self, api_client, supermarket):
        Product.objects.create(
            name="Aardappelen", external_id="ext-a", supermarket=supermarket, is_available=True, has_discount=False
        )
        Product.objects.create(
            name="Boter", external_id="ext-b", supermarket=supermarket, is_available=True, has_discount=True
        )
        response = api_client.get(SEARCH_URL)
        assert response.data["results"][0]["name"] == "Boter"

    def test_pagination(self, api_client, supermarket):
        for i in range(25):
            Product.objects.create(
                name=f"Product {i:02d}", external_id=f"ext-{i}", supermarket=supermarket, is_available=True
            )
        response = api_client.get(SEARCH_URL, {"page_size": 10})
        assert response.status_code == 200
        assert response.data["count"] == 25
        assert len(response.data["results"]) == 10
        assert response.data["next"] is not None

    def test_returns_expected_fields(self, api_client, product):
        response = api_client.get(SEARCH_URL)
        item = response.data["results"][0]
        for field in [
            "id",
            "name",
            "supermarket",
            "category",
            "base_price",
            "current_price",
            "has_discount",
            "discount_text",
            "image_url",
            "website_url",
            "is_tracked",
        ]:
            assert field in item

    def test_category_is_nested_object(self, api_client, product):
        response = api_client.get(SEARCH_URL)
        cat = response.data["results"][0]["category"]
        assert isinstance(cat, dict)
        assert "id" in cat
        assert "name" in cat
        assert "parent" in cat

    def test_is_tracked_false_by_default(self, api_client, product):
        response = api_client.get(SEARCH_URL)
        assert response.data["results"][0]["is_tracked"] is False

    def test_is_tracked_true_when_tracked(self, api_client, user, product):
        UserTrackedProduct.objects.create(user_id=user.uid, product=product)
        response = api_client.get(SEARCH_URL)
        assert response.data["results"][0]["is_tracked"] is True

    def test_requires_authentication(self):
        response = APIClient().get(SEARCH_URL)
        assert response.status_code == 401


@pytest.mark.django_db
class TestProductTracking:
    def _track_url(self, product_id):
        return f"/v1/products/{product_id}/track"

    def test_track_product(self, api_client, product):
        response = api_client.post(self._track_url(product.id))
        assert response.status_code == 204
        assert UserTrackedProduct.objects.filter(product=product).exists()

    def test_track_idempotent(self, api_client, product):
        api_client.post(self._track_url(product.id))
        response = api_client.post(self._track_url(product.id))
        assert response.status_code == 204
        assert UserTrackedProduct.objects.filter(product=product).count() == 1

    def test_untrack_product(self, api_client, user, product):
        UserTrackedProduct.objects.create(user_id=user.uid, product=product)
        response = api_client.delete(self._track_url(product.id))
        assert response.status_code == 204
        assert not UserTrackedProduct.objects.filter(product=product).exists()

    def test_untrack_not_tracked(self, api_client, product):
        response = api_client.delete(self._track_url(product.id))
        assert response.status_code == 204

    def test_post_unknown_product(self, api_client):
        response = api_client.post(self._track_url(99999))
        assert response.status_code == 404
        assert "errors" in response.data
        assert response.data["errors"][0]["code"] == "not_found"

    def test_requires_auth(self, product):
        client = APIClient()
        assert client.post(self._track_url(product.id)).status_code == 401
        assert client.delete(self._track_url(product.id)).status_code == 401


@pytest.mark.django_db
class TestDeals:
    def test_returns_only_tracked_discounted(self, api_client, user, supermarket, category):
        tracked_discounted = Product.objects.create(
            name="Kaas",
            external_id="ext-1",
            supermarket=supermarket,
            category=category,
            has_discount=True,
            is_available=True,
        )
        tracked_no_discount = Product.objects.create(
            name="Melk",
            external_id="ext-2",
            supermarket=supermarket,
            category=category,
            has_discount=False,
            is_available=True,
        )
        untracked_discounted = Product.objects.create(
            name="Boter",
            external_id="ext-3",
            supermarket=supermarket,
            category=category,
            has_discount=True,
            is_available=True,
        )
        UserTrackedProduct.objects.create(user_id=user.uid, product=tracked_discounted)
        UserTrackedProduct.objects.create(user_id=user.uid, product=tracked_no_discount)

        response = api_client.get(DEALS_URL)
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["id"] == tracked_discounted.id

    def test_supermarket_filter(self, api_client, user, supermarket, supermarket2, category):
        p1 = Product.objects.create(
            name="Kaas AH",
            external_id="ext-ah",
            supermarket=supermarket,
            category=category,
            has_discount=True,
            is_available=True,
        )
        p2 = Product.objects.create(
            name="Kaas Jumbo",
            external_id="ext-jb",
            supermarket=supermarket2,
            has_discount=True,
            is_available=True,
        )
        UserTrackedProduct.objects.create(user_id=user.uid, product=p1)
        UserTrackedProduct.objects.create(user_id=user.uid, product=p2)

        response = api_client.get(DEALS_URL, {"supermarket": supermarket2.id})
        assert response.data["count"] == 1
        assert response.data["results"][0]["id"] == p2.id

    def test_empty_when_no_tracked(self, api_client):
        response = api_client.get(DEALS_URL)
        assert response.status_code == 200
        assert response.data["count"] == 0
        assert response.data["results"] == []

    def test_requires_auth(self):
        response = APIClient().get(DEALS_URL)
        assert response.status_code == 401
