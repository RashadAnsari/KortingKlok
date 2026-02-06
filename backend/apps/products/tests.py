import uuid
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from users.models import UserDevice, UserTopicSecret

from products.models import Category, PriceHistory, Product, Supermarket, UserTrackedProduct
from products.notifications.tasks import (
    _build_notification,
    _format_price,
    notify_price_changes,
    notify_user_price_change,
)
from products.scrapers.base import BaseSupermarketScraper
from products.scrapers.dtos import ScrapedCategory, ScrapedProduct
from products.scrapers.persists import (
    _has_price_changed,
    get_supermarket,
    sync_categories,
    sync_products,
)
from products.scrapers.registry import _REGISTRY, get_all_slugs, get_scraper, register_scraper

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def supermarket(db):
    return Supermarket.objects.create(name="Albert Heijn", slug="ah")


@pytest.fixture
def run_id():
    return uuid.uuid4()


@pytest.fixture
def scraped_categories():
    return [
        ScrapedCategory(external_id="cat-1", name="Zuivel"),
        ScrapedCategory(external_id="cat-2", name="Kaas", parent_external_id="cat-1"),
    ]


@pytest.fixture
def scraped_products():
    return [
        ScrapedProduct(
            external_id="prod-1",
            name="Melk",
            base_price=Decimal("1.50"),
            current_price=Decimal("1.29"),
            has_discount=True,
            discount_text="2 voor 2.00",
            category_external_id="cat-1",
        ),
        ScrapedProduct(
            external_id="prod-2",
            name="Kaas Jong",
            base_price=Decimal("4.99"),
            current_price=Decimal("4.99"),
        ),
    ]


# ---------------------------------------------------------------------------
# DTOs
# ---------------------------------------------------------------------------


class TestScrapedCategory:
    def test_create_with_required_fields(self):
        cat = ScrapedCategory(external_id="c1", name="Fruit")
        assert cat.external_id == "c1"
        assert cat.name == "Fruit"
        assert cat.parent_external_id is None

    def test_create_with_parent(self):
        cat = ScrapedCategory(external_id="c2", name="Appels", parent_external_id="c1")
        assert cat.parent_external_id == "c1"

    def test_is_frozen(self):
        cat = ScrapedCategory(external_id="c1", name="Fruit")
        with pytest.raises(AttributeError):
            cat.name = "Groente"


class TestScrapedProduct:
    def test_create_with_required_fields(self):
        prod = ScrapedProduct(external_id="p1", name="Appel")
        assert prod.external_id == "p1"
        assert prod.name == "Appel"
        assert prod.base_price is None
        assert prod.current_price is None
        assert prod.has_discount is False
        assert prod.discount_text is None
        assert prod.image_url is None
        assert prod.website_url is None
        assert prod.category_external_id is None

    def test_create_with_all_fields(self):
        prod = ScrapedProduct(
            external_id="p1",
            name="Appel",
            base_price=Decimal("1.00"),
            current_price=Decimal("0.79"),
            has_discount=True,
            discount_text="Aanbieding",
            image_url="https://example.com/img.jpg",
            website_url="https://example.com/appel",
            category_external_id="c1",
        )
        assert prod.current_price == Decimal("0.79")
        assert prod.has_discount is True

    def test_is_frozen(self):
        prod = ScrapedProduct(external_id="p1", name="Appel")
        with pytest.raises(AttributeError):
            prod.name = "Peer"


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


class TestRegistry:
    def setup_method(self):
        self._original_registry = _REGISTRY.copy()
        _REGISTRY.clear()

    def teardown_method(self):
        _REGISTRY.clear()
        _REGISTRY.update(self._original_registry)

    def test_register_and_get_scraper(self):
        @register_scraper
        class TestScraper(BaseSupermarketScraper):
            supermarket_slug = "test-market"

            def scrape_categories(self):
                return []

            def scrape_products(self):
                return []

        scraper = get_scraper("test-market")
        assert isinstance(scraper, TestScraper)

    def test_register_duplicate_slug_raises(self):
        @register_scraper
        class Scraper1(BaseSupermarketScraper):
            supermarket_slug = "dup"

            def scrape_categories(self):
                return []

            def scrape_products(self):
                return []

        with pytest.raises(ValueError, match="already registered"):

            @register_scraper
            class Scraper2(BaseSupermarketScraper):
                supermarket_slug = "dup"

                def scrape_categories(self):
                    return []

                def scrape_products(self):
                    return []

    def test_get_scraper_unknown_slug_raises(self):
        with pytest.raises(ValueError, match="No scraper registered"):
            get_scraper("nonexistent")

    def test_get_all_slugs(self):
        @register_scraper
        class ScraperA(BaseSupermarketScraper):
            supermarket_slug = "alpha"

            def scrape_categories(self):
                return []

            def scrape_products(self):
                return []

        @register_scraper
        class ScraperB(BaseSupermarketScraper):
            supermarket_slug = "beta"

            def scrape_categories(self):
                return []

            def scrape_products(self):
                return []

        slugs = get_all_slugs()
        assert "alpha" in slugs
        assert "beta" in slugs


# ---------------------------------------------------------------------------
# Persistence – sync_categories
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestSyncCategories:
    def test_creates_categories(self, supermarket, scraped_categories):
        category_map = sync_categories(supermarket, scraped_categories)
        assert len(category_map) == 2
        assert Category.objects.filter(supermarket=supermarket).count() == 2

    def test_sets_parent_relationship(self, supermarket, scraped_categories):
        category_map = sync_categories(supermarket, scraped_categories)
        child = category_map["cat-2"]
        parent = category_map["cat-1"]
        child.refresh_from_db()
        assert child.parent_id == parent.id

    def test_updates_existing_category_name(self, supermarket):
        Category.objects.create(supermarket=supermarket, external_id="cat-1", name="Old Name")
        scraped = [ScrapedCategory(external_id="cat-1", name="New Name")]
        category_map = sync_categories(supermarket, scraped)
        assert category_map["cat-1"].name == "New Name"
        assert Category.objects.filter(supermarket=supermarket).count() == 1

    def test_empty_list_returns_empty_map(self, supermarket):
        category_map = sync_categories(supermarket, [])
        assert category_map == {}


# ---------------------------------------------------------------------------
# Persistence – sync_products
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestSyncProducts:
    def test_creates_new_products(self, supermarket, scraped_products, run_id):
        stats = sync_products(supermarket, scraped_products, run_id=run_id)
        assert stats["created"] == 2
        assert stats["updated"] == 0
        assert Product.objects.filter(supermarket=supermarket).count() == 2

    def test_creates_price_history_for_new_products(self, supermarket, scraped_products, run_id):
        sync_products(supermarket, scraped_products, run_id=run_id)
        assert PriceHistory.objects.filter(run_id=run_id).count() == 2

    def test_updates_existing_product(self, supermarket, run_id):
        Product.objects.create(
            supermarket=supermarket,
            external_id="prod-1",
            name="Old Name",
            base_price=Decimal("1.00"),
            current_price=Decimal("1.00"),
        )
        scraped = [
            ScrapedProduct(
                external_id="prod-1",
                name="New Name",
                base_price=Decimal("1.50"),
                current_price=Decimal("1.29"),
                has_discount=True,
            ),
        ]
        stats = sync_products(supermarket, scraped, run_id=run_id)
        assert stats["updated"] == 1
        assert stats["created"] == 0
        product = Product.objects.get(supermarket=supermarket, external_id="prod-1")
        assert product.name == "New Name"
        assert product.current_price == Decimal("1.29")

    def test_creates_price_history_on_price_change(self, supermarket, run_id):
        Product.objects.create(
            supermarket=supermarket,
            external_id="prod-1",
            name="Melk",
            base_price=Decimal("1.50"),
            current_price=Decimal("1.50"),
        )
        scraped = [
            ScrapedProduct(
                external_id="prod-1",
                name="Melk",
                base_price=Decimal("1.50"),
                current_price=Decimal("1.29"),
                has_discount=True,
                discount_text="Aanbieding",
            ),
        ]
        stats = sync_products(supermarket, scraped, run_id=run_id)
        assert stats["price_changes"] == 1
        assert PriceHistory.objects.filter(run_id=run_id).count() == 1

    def test_no_price_history_when_price_unchanged(self, supermarket, run_id):
        Product.objects.create(
            supermarket=supermarket,
            external_id="prod-1",
            name="Melk",
            base_price=Decimal("1.50"),
            current_price=Decimal("1.50"),
        )
        scraped = [
            ScrapedProduct(
                external_id="prod-1",
                name="Melk",
                base_price=Decimal("1.50"),
                current_price=Decimal("1.50"),
            ),
        ]
        stats = sync_products(supermarket, scraped, run_id=run_id)
        assert stats["price_changes"] == 0
        assert PriceHistory.objects.filter(run_id=run_id).count() == 0

    def test_marks_unseen_products_unavailable(self, supermarket, run_id):
        Product.objects.create(
            supermarket=supermarket,
            external_id="old-prod",
            name="Old Product",
            is_available=True,
        )
        scraped = [ScrapedProduct(external_id="new-prod", name="New Product")]
        stats = sync_products(supermarket, scraped, run_id=run_id)
        assert stats["marked_unavailable"] == 1
        old = Product.objects.get(external_id="old-prod")
        assert old.is_available is False

    def test_assigns_category_from_map(self, supermarket, run_id, scraped_categories):
        category_map = sync_categories(supermarket, scraped_categories)
        scraped = [
            ScrapedProduct(
                external_id="prod-1",
                name="Melk",
                category_external_id="cat-1",
            ),
        ]
        sync_products(supermarket, scraped, category_map, run_id=run_id)
        product = Product.objects.get(external_id="prod-1")
        assert product.category == category_map["cat-1"]

    def test_price_history_has_run_id(self, supermarket, scraped_products, run_id):
        sync_products(supermarket, scraped_products, run_id=run_id)
        for ph in PriceHistory.objects.filter(run_id=run_id):
            assert ph.run_id == run_id


# ---------------------------------------------------------------------------
# Persistence – _has_price_changed
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestHasPriceChanged:
    def test_detects_current_price_change(self, supermarket):
        product = Product.objects.create(
            supermarket=supermarket,
            external_id="p1",
            name="Test",
            base_price=Decimal("1.00"),
            current_price=Decimal("1.00"),
        )
        scraped = ScrapedProduct(
            external_id="p1",
            name="Test",
            base_price=Decimal("1.00"),
            current_price=Decimal("0.80"),
        )
        assert _has_price_changed(product, scraped) is True

    def test_detects_base_price_change(self, supermarket):
        product = Product.objects.create(
            supermarket=supermarket,
            external_id="p1",
            name="Test",
            base_price=Decimal("1.00"),
            current_price=Decimal("1.00"),
        )
        scraped = ScrapedProduct(
            external_id="p1",
            name="Test",
            base_price=Decimal("1.50"),
            current_price=Decimal("1.00"),
        )
        assert _has_price_changed(product, scraped) is True

    def test_detects_discount_status_change(self, supermarket):
        product = Product.objects.create(
            supermarket=supermarket,
            external_id="p1",
            name="Test",
            base_price=Decimal("1.00"),
            current_price=Decimal("1.00"),
            has_discount=False,
        )
        scraped = ScrapedProduct(
            external_id="p1",
            name="Test",
            base_price=Decimal("1.00"),
            current_price=Decimal("1.00"),
            has_discount=True,
        )
        assert _has_price_changed(product, scraped) is True

    def test_no_change_returns_false(self, supermarket):
        product = Product.objects.create(
            supermarket=supermarket,
            external_id="p1",
            name="Test",
            base_price=Decimal("1.00"),
            current_price=Decimal("1.00"),
            has_discount=False,
            discount_text=None,
        )
        scraped = ScrapedProduct(
            external_id="p1",
            name="Test",
            base_price=Decimal("1.00"),
            current_price=Decimal("1.00"),
            has_discount=False,
            discount_text=None,
        )
        assert _has_price_changed(product, scraped) is False


# ---------------------------------------------------------------------------
# Persistence – get_supermarket
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestGetSupermarket:
    def test_returns_supermarket_by_slug(self, supermarket):
        result = get_supermarket("ah")
        assert result.id == supermarket.id

    def test_raises_for_unknown_slug(self):
        with pytest.raises(Supermarket.DoesNotExist):
            get_supermarket("nonexistent")


# ---------------------------------------------------------------------------
# Scraper tasks
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestScrapeTask:
    @patch("products.scrapers.tasks.get_scraper")
    def test_scrape_supermarket_calls_scraper_and_syncs(self, mock_get_scraper, supermarket):
        from products.scrapers.tasks import scrape_supermarket

        mock_scraper = MagicMock()
        mock_scraper.scrape_categories.return_value = [
            ScrapedCategory(external_id="c1", name="Zuivel"),
        ]
        mock_scraper.scrape_products.return_value = [
            ScrapedProduct(
                external_id="p1",
                name="Melk",
                base_price=Decimal("1.50"),
                current_price=Decimal("1.29"),
            ),
        ]
        mock_get_scraper.return_value = mock_scraper

        result = scrape_supermarket("ah")

        mock_scraper.scrape_categories.assert_called_once()
        mock_scraper.scrape_products.assert_called_once()
        mock_scraper.close.assert_called_once()
        assert result["supermarket"] == "ah"
        assert result["categories_synced"] == 1
        assert result["created"] == 1

    @patch("products.scrapers.tasks.get_scraper")
    def test_scrape_supermarket_closes_scraper_on_error(self, mock_get_scraper, supermarket):
        from products.scrapers.tasks import scrape_supermarket

        mock_scraper = MagicMock()
        mock_scraper.scrape_categories.side_effect = RuntimeError("API down")
        mock_get_scraper.return_value = mock_scraper

        with pytest.raises(RuntimeError, match="API down"):
            scrape_supermarket("ah")

        mock_scraper.close.assert_called_once()

    @patch("products.scrapers.tasks.get_scraper")
    @patch("products.notifications.tasks.notify_price_changes.delay")
    def test_scrape_dispatches_notification_on_price_changes(self, mock_notify, mock_get_scraper, supermarket):
        from products.scrapers.tasks import scrape_supermarket

        mock_scraper = MagicMock()
        mock_scraper.scrape_categories.return_value = []
        mock_scraper.scrape_products.return_value = [
            ScrapedProduct(external_id="p1", name="Melk", base_price=Decimal("1.50"), current_price=Decimal("1.29")),
        ]
        mock_get_scraper.return_value = mock_scraper

        result = scrape_supermarket("ah")

        assert result["price_changes"] == 1
        mock_notify.assert_called_once()
        call_args = mock_notify.call_args[0]
        assert call_args[1] == "ah"

    @patch("products.scrapers.tasks.get_scraper")
    @patch("products.notifications.tasks.notify_price_changes.delay")
    def test_scrape_does_not_dispatch_notification_without_price_changes(
        self, mock_notify, mock_get_scraper, supermarket
    ):
        from products.scrapers.tasks import scrape_supermarket

        Product.objects.create(
            supermarket=supermarket,
            external_id="p1",
            name="Melk",
            base_price=Decimal("1.50"),
            current_price=Decimal("1.50"),
        )
        mock_scraper = MagicMock()
        mock_scraper.scrape_categories.return_value = []
        mock_scraper.scrape_products.return_value = [
            ScrapedProduct(external_id="p1", name="Melk", base_price=Decimal("1.50"), current_price=Decimal("1.50")),
        ]
        mock_get_scraper.return_value = mock_scraper

        result = scrape_supermarket("ah")

        assert result["price_changes"] == 0
        mock_notify.assert_not_called()

    @patch("products.scrapers.tasks.scrape_supermarket.delay")
    @patch("products.scrapers.registry.get_all_slugs", return_value=["ah", "jumbo"])
    def test_scrape_all_command_dispatches_per_slug(self, mock_slugs, mock_delay):
        from django.core.management import call_command

        mock_delay.return_value = MagicMock(id="task-123")
        call_command("scrape_all_supermarkets")
        assert mock_delay.call_count == 2
        mock_delay.assert_any_call("ah")
        mock_delay.assert_any_call("jumbo")


# ---------------------------------------------------------------------------
# Notification tasks
# ---------------------------------------------------------------------------


@pytest.fixture
def notification_setup(db):
    """Create a complete setup for notification tests."""
    supermarket = Supermarket.objects.create(name="Albert Heijn", slug="ah")
    run_id = uuid.uuid4()

    product = Product.objects.create(
        supermarket=supermarket,
        external_id="p1",
        name="Melk",
        base_price=Decimal("1.50"),
        current_price=Decimal("1.29"),
        has_discount=True,
        discount_text="2 voor 2.00",
    )
    PriceHistory.objects.create(
        product=product,
        base_price=Decimal("1.50"),
        price=Decimal("1.29"),
        has_discount=True,
        discount_text="2 voor 2.00",
        run_id=run_id,
    )
    UserTrackedProduct.objects.create(
        user_id="user-1",
        product=product,
        notification_enabled=True,
    )
    UserDevice.objects.create(
        user_id="user-1",
        device_id="dev-1",
        fcm_token="token-1",
        device_type="ios",
        language="nl",
    )
    return {
        "supermarket": supermarket,
        "run_id": run_id,
        "product": product,
    }


@pytest.mark.django_db
class TestNotifyPriceChanges:
    @patch("products.notifications.tasks.notify_user_price_change.delay")
    def test_dispatches_per_user_task(self, mock_delay, notification_setup):
        run_id = notification_setup["run_id"]
        result = notify_price_changes(str(run_id), "ah")
        assert result["users_dispatched"] == 1
        mock_delay.assert_called_once()
        call_args = mock_delay.call_args[0]
        assert call_args[0] == str(run_id)
        assert call_args[1] == "ah"
        assert call_args[2] == "user-1"

    @patch("products.notifications.tasks.notify_user_price_change.delay")
    def test_no_dispatch_when_no_price_entries(self, mock_delay):
        run_id = uuid.uuid4()
        result = notify_price_changes(str(run_id), "ah")
        assert result["users_dispatched"] == 0
        mock_delay.assert_not_called()

    @patch("products.notifications.tasks.notify_user_price_change.delay")
    def test_no_dispatch_when_no_tracking_users(self, mock_delay, notification_setup):
        UserTrackedProduct.objects.all().delete()
        run_id = notification_setup["run_id"]
        result = notify_price_changes(str(run_id), "ah")
        assert result["users_dispatched"] == 0
        mock_delay.assert_not_called()

    @patch("products.notifications.tasks.notify_user_price_change.delay")
    def test_skips_users_with_notifications_disabled(self, mock_delay, notification_setup):
        UserTrackedProduct.objects.all().update(notification_enabled=False)
        run_id = notification_setup["run_id"]
        result = notify_price_changes(str(run_id), "ah")
        assert result["users_dispatched"] == 0
        mock_delay.assert_not_called()

    @patch("products.notifications.tasks.notify_user_price_change.delay")
    def test_dispatches_for_multiple_users(self, mock_delay, notification_setup):
        product = notification_setup["product"]
        UserTrackedProduct.objects.create(user_id="user-2", product=product, notification_enabled=True)
        run_id = notification_setup["run_id"]
        result = notify_price_changes(str(run_id), "ah")
        assert result["users_dispatched"] == 2
        assert mock_delay.call_count == 2

    @patch("products.notifications.tasks.notify_user_price_change.delay")
    def test_no_dispatch_when_price_change_has_no_discount(self, mock_delay, db):
        supermarket = Supermarket.objects.create(name="Albert Heijn", slug="ah")
        run_id = uuid.uuid4()
        product = Product.objects.create(
            supermarket=supermarket,
            external_id="p1",
            name="Melk",
            base_price=Decimal("1.50"),
            current_price=Decimal("1.29"),
            has_discount=False,
        )
        PriceHistory.objects.create(
            product=product,
            base_price=Decimal("1.50"),
            price=Decimal("1.29"),
            has_discount=False,
            run_id=run_id,
        )
        UserTrackedProduct.objects.create(user_id="user-1", product=product, notification_enabled=True)
        result = notify_price_changes(str(run_id), "ah")
        assert result["users_dispatched"] == 0
        mock_delay.assert_not_called()


@pytest.mark.django_db
class TestNotifyUserPriceChange:
    @patch("products.notifications.tasks.messaging.send")
    def test_sends_fcm_message(self, mock_send, notification_setup):
        setup = notification_setup
        product = setup["product"]
        result = notify_user_price_change(str(setup["run_id"]), "ah", "user-1", [product.id])
        assert result["notifications_sent"] == 1
        mock_send.assert_called_once()

    @patch("products.notifications.tasks.messaging.send")
    def test_sends_to_each_device_language(self, mock_send, notification_setup):
        setup = notification_setup
        product = setup["product"]
        UserDevice.objects.create(
            user_id="user-1",
            device_id="dev-2",
            fcm_token="token-2",
            device_type="android",
            language="en",
        )
        result = notify_user_price_change(str(setup["run_id"]), "ah", "user-1", [product.id])
        assert result["notifications_sent"] == 2
        assert mock_send.call_count == 2

    @patch("products.notifications.tasks.messaging.send")
    def test_returns_zero_when_no_price_entries(self, mock_send, notification_setup):
        result = notify_user_price_change(str(notification_setup["run_id"]), "ah", "user-1", [99999])
        assert result["notifications_sent"] == 0
        mock_send.assert_not_called()

    @patch("products.notifications.tasks.messaging.send")
    def test_defaults_to_nl_when_no_devices(self, mock_send, notification_setup):
        setup = notification_setup
        product = setup["product"]
        UserDevice.objects.all().delete()
        result = notify_user_price_change(str(setup["run_id"]), "ah", "user-1", [product.id])
        assert result["notifications_sent"] == 1
        mock_send.assert_called_once()

    @patch("products.notifications.tasks.messaging.send", side_effect=Exception("FCM error"))
    def test_handles_fcm_error_gracefully(self, mock_send, notification_setup):
        setup = notification_setup
        product = setup["product"]
        result = notify_user_price_change(str(setup["run_id"]), "ah", "user-1", [product.id])
        assert result["notifications_sent"] == 0

    @patch("products.notifications.tasks.messaging.send")
    def test_skips_non_discounted_entries(self, mock_send, notification_setup):
        setup = notification_setup
        supermarket = setup["supermarket"]
        run_id = setup["run_id"]
        non_discount_product = Product.objects.create(
            supermarket=supermarket,
            external_id="p2",
            name="Brood",
            base_price=Decimal("2.00"),
            current_price=Decimal("1.80"),
            has_discount=False,
        )
        PriceHistory.objects.create(
            product=non_discount_product,
            base_price=Decimal("2.00"),
            price=Decimal("1.80"),
            has_discount=False,
            run_id=run_id,
        )
        result = notify_user_price_change(str(run_id), "ah", "user-1", [non_discount_product.id])
        assert result["notifications_sent"] == 0
        mock_send.assert_not_called()

    @patch("products.notifications.tasks.messaging.send")
    def test_message_uses_correct_topic(self, mock_send, notification_setup):
        setup = notification_setup
        product = setup["product"]
        notify_user_price_change(str(setup["run_id"]), "ah", "user-1", [product.id])
        message = mock_send.call_args[0][0]
        expected_topic = UserTopicSecret.get_topic_name("user-1", "nl")
        assert message.topic == expected_topic


# ---------------------------------------------------------------------------
# Notification helpers
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestBuildNotification:
    def test_single_product_notification(self, supermarket, run_id):
        product = Product.objects.create(
            supermarket=supermarket,
            external_id="p1",
            name="Melk",
            current_price=Decimal("1.29"),
        )
        entry = PriceHistory.objects.create(
            product=product,
            price=Decimal("1.29"),
            has_discount=False,
            run_id=run_id,
        )
        price_lookup = {product.id: entry}
        payload = _build_notification([product], price_lookup, "ah")
        assert payload["data"]["type"] == "price_change"
        assert payload["data"]["product_count"] == "1"
        assert payload["data"]["product_id"] == str(product.id)
        assert payload["data"]["product_external_id"] == "p1"

    def test_multiple_products_notification(self, supermarket, run_id):
        products = []
        price_lookup = {}
        for i in range(3):
            product = Product.objects.create(
                supermarket=supermarket,
                external_id=f"p{i}",
                name=f"Product {i}",
                current_price=Decimal("1.00"),
            )
            entry = PriceHistory.objects.create(
                product=product,
                price=Decimal("1.00"),
                run_id=run_id,
            )
            products.append(product)
            price_lookup[product.id] = entry

        payload = _build_notification(products, price_lookup, "ah")
        assert payload["data"]["product_count"] == "3"
        assert "product_id" not in payload["data"]

    def test_single_product_with_discount_text(self, supermarket, run_id):
        product = Product.objects.create(
            supermarket=supermarket,
            external_id="p1",
            name="Melk",
            current_price=Decimal("1.29"),
        )
        entry = PriceHistory.objects.create(
            product=product,
            price=Decimal("1.29"),
            has_discount=True,
            discount_text="2 voor 2.00",
            run_id=run_id,
        )
        price_lookup = {product.id: entry}
        payload = _build_notification([product], price_lookup, "ah")
        assert "2 voor 2.00" in payload["body"]


class TestFormatPrice:
    def test_formats_decimal_price(self):
        assert _format_price(Decimal("1.29")) == "\u20ac1.29"

    def test_formats_whole_number(self):
        assert _format_price(Decimal("5.00")) == "\u20ac5.00"

    def test_none_returns_translated_unknown(self):
        result = _format_price(None)
        # Default language is "nl", so gettext returns the Dutch translation
        assert result in ("unknown", "onbekend")
