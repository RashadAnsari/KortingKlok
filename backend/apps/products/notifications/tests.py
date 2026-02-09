import uuid
from decimal import Decimal
from unittest.mock import patch

import pytest
from users.models import UserDevice, UserTopicSecret

from products.models import PriceHistory, Product, Supermarket, UserTrackedProduct
from products.notifications.tasks import (
    _build_notification,
    _format_price,
    notify_price_changes,
    notify_user_price_change,
)

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


# ---------------------------------------------------------------------------
# Notification tasks
# ---------------------------------------------------------------------------


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
    def test_dispatches_for_multiple_users(self, mock_delay, notification_setup):
        product = notification_setup["product"]
        UserTrackedProduct.objects.create(user_id="user-2", product=product)
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
        UserTrackedProduct.objects.create(user_id="user-1", product=product)
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
