import uuid
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from products.models import Category, PriceHistory, Product, Supermarket
from products.scrapers.base import BaseSupermarketScraper
from products.scrapers.dtos import ScrapedCategory, ScrapedProduct
from products.scrapers.persists import (
    _has_price_changed,
    get_supermarket,
    sync_categories,
    sync_products,
)
from products.scrapers.registry import _REGISTRY, get_all_slugs, get_scraper, register_scraper


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


@pytest.mark.django_db
class TestGetSupermarket:
    def test_returns_supermarket_by_slug(self, supermarket):
        result = get_supermarket("ah")
        assert result.id == supermarket.id

    def test_raises_for_unknown_slug(self):
        with pytest.raises(Supermarket.DoesNotExist):
            get_supermarket("nonexistent")


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

    @patch("products.scrapers.tasks.scrape_supermarket.apply_async")
    @patch("products.scrapers.registry.get_all_slugs", return_value=["ah", "jumbo"])
    def test_scrape_all_command_dispatches_per_slug(self, mock_slugs, mock_apply_async):
        from django.core.management import call_command

        mock_apply_async.return_value = MagicMock(id="task-123")
        call_command("scrape_all_supermarkets")
        assert mock_apply_async.call_count == 2
        mock_apply_async.assert_any_call(("ah",))
        mock_apply_async.assert_any_call(("jumbo",))
