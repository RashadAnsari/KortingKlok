import logging
import uuid
from collections import defaultdict

from django.utils import translation
from django.utils.translation import gettext as _

from firebase_admin import messaging
from users.models import UserDevice, UserTopicSecret
from utils.tasks import BaseTaskWithRetry

from baseapi.celery import app
from products.models import PriceHistory, UserTrackedProduct

logger = logging.getLogger("notifications.tasks")


@app.task(base=BaseTaskWithRetry, name="notify_price_changes")
def notify_price_changes(run_id_str: str, supermarket_slug: str) -> dict:
    """Dispatch per-user notification tasks for products whose prices changed.

    Queries PriceHistory entries for the given run_id, finds users tracking
    those products with notifications enabled, and dispatches an individual
    notification task for each user.
    """
    run_id = uuid.UUID(run_id_str)
    logger.info("Processing notifications for run_id=%s, supermarket=%s", run_id, supermarket_slug)

    price_entries = PriceHistory.objects.filter(run_id=run_id, has_discount=True).select_related("product")

    if not price_entries.exists():
        logger.info("No discounted price entries for run_id=%s, skipping notifications", run_id)
        return {"run_id": run_id_str, "users_dispatched": 0}

    product_ids = set(price_entries.values_list("product_id", flat=True))
    logger.info("Found %d discounted products in run_id=%s", len(product_ids), run_id)

    tracked = UserTrackedProduct.objects.filter(
        product_id__in=product_ids,
        notification_enabled=True,
    )

    if not tracked.exists():
        logger.info("No users tracking changed products for run_id=%s", run_id)
        return {"run_id": run_id_str, "users_dispatched": 0}

    user_product_ids: dict[str, list[int]] = defaultdict(list)
    for utp in tracked:
        user_product_ids[utp.user_id].append(utp.product_id)

    logger.info("Dispatching notification tasks for %d users for run_id=%s", len(user_product_ids), run_id)

    for user_id, product_id_list in user_product_ids.items():
        notify_user_price_change.delay(run_id_str, supermarket_slug, user_id, product_id_list)

    return {
        "run_id": run_id_str,
        "supermarket": supermarket_slug,
        "users_dispatched": len(user_product_ids),
    }


@app.task(base=BaseTaskWithRetry, name="notify_user_price_change")
def notify_user_price_change(
    run_id_str: str,
    supermarket_slug: str,
    user_id: str,
    product_ids: list[int],
) -> dict:
    """Send FCM notifications to a single user for their tracked price changes.

    Sends a language-specific FCM message for each device language the user has.
    """
    run_id = uuid.UUID(run_id_str)

    price_entries = PriceHistory.objects.filter(
        run_id=run_id,
        product_id__in=product_ids,
        has_discount=True,
    ).select_related("product")

    products = [entry.product for entry in price_entries]
    price_lookup = {entry.product_id: entry for entry in price_entries}

    if not products:
        logger.info("No price entries found for user %s run_id=%s, skipping", user_id, run_id)
        return {"user_id": user_id, "notifications_sent": 0}

    languages = set(UserDevice.objects.filter(user_id=user_id).values_list("language", flat=True).distinct()) or {"nl"}

    notifications_sent = 0

    for language in languages:
        try:
            translation.activate(language)
            topic = UserTopicSecret.get_topic_name(user_id, language)
            payload = _build_notification(products, price_lookup, supermarket_slug)
            message = messaging.Message(
                topic=topic,
                notification=messaging.Notification(
                    title=payload["title"],
                    body=payload["body"],
                ),
                data=payload["data"],
            )
            messaging.send(message)
            notifications_sent += 1
            logger.debug("Sent notification to user %s on topic %s (%s)", user_id, topic, language)
        except Exception:
            logger.exception("Failed to send notification to user %s (%s)", user_id, language)
        finally:
            translation.deactivate()

    return {
        "user_id": user_id,
        "run_id": run_id_str,
        "notifications_sent": notifications_sent,
    }


def _build_notification(
    products: list,
    price_lookup: dict,
    supermarket_slug: str,
) -> dict:
    """Build the FCM notification payload for a user.

    Uses the currently activated language for translated strings.
    Single product: show name and current price.
    Multiple products: show a summary count.
    """
    if len(products) == 1:
        product = products[0]
        entry = price_lookup.get(product.id)
        title = _("Price change")
        body = _("%(name)s is now %(price)s") % {"name": product.name, "price": _format_price(product.current_price)}
        if entry and entry.has_discount and entry.discount_text:
            body += f" ({entry.discount_text})"
    else:
        title = _("Price changes")
        body = _("%(count)d products you follow have new prices") % {"count": len(products)}

    data = {
        "type": "price_change",
        "supermarket": supermarket_slug,
        "product_count": str(len(products)),
    }

    if len(products) == 1:
        product = products[0]
        data["product_id"] = str(product.id)
        data["product_external_id"] = product.external_id

    return {"title": title, "body": body, "data": data}


def _format_price(price) -> str:
    """Format a Decimal price for display."""
    if price is None:
        return _("unknown")
    return f"\u20ac{price:.2f}"
