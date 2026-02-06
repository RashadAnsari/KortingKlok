import logging
import uuid

from django.db import transaction

from utils.tasks import BaseTaskWithRetry

from baseapi.celery import app
from products.scrapers.persists import get_supermarket, sync_categories, sync_products
from products.scrapers.registry import get_all_slugs, get_scraper

logger = logging.getLogger("scrapers.tasks")


@app.task(base=BaseTaskWithRetry, name="scrape_supermarket")
def scrape_supermarket(supermarket_slug: str) -> dict:
    """Scrape all categories and products for a single supermarket.

    Generates a unique run_id to tag all PriceHistory entries created during
    this run, then dispatches a notification task for any price changes.
    """
    logger.info("Starting scrape for %s", supermarket_slug)

    run_id = uuid.uuid4()
    supermarket = get_supermarket(supermarket_slug)
    scraper = get_scraper(supermarket_slug)

    try:
        scraped_categories = scraper.scrape_categories()
        logger.info("Scraped %d categories for %s", len(scraped_categories), supermarket_slug)

        scraped_products = scraper.scrape_products()
        logger.info("Scraped %d products for %s", len(scraped_products), supermarket_slug)

        with transaction.atomic():
            category_map = sync_categories(supermarket, scraped_categories)
            product_stats = sync_products(supermarket, scraped_products, category_map, run_id=run_id)

        result = {
            "supermarket": supermarket_slug,
            "run_id": str(run_id),
            "categories_synced": len(scraped_categories),
            **product_stats,
        }
        logger.info("Completed scrape for %s: %s", supermarket_slug, result)

        if product_stats.get("price_changes", 0) > 0:
            from products.notifications.tasks import notify_price_changes

            notify_price_changes.delay(str(run_id), supermarket_slug)
            logger.info("Dispatched notification task for run_id=%s", run_id)

        return result
    finally:
        scraper.close()


@app.task(base=BaseTaskWithRetry, name="scrape_all_supermarkets")
def scrape_all_supermarkets() -> list[str]:
    """Dispatch individual scrape tasks for every registered supermarket.

    Intended for Celery Beat scheduling (e.g., daily).
    """
    slugs = get_all_slugs()
    task_ids = []
    for slug in slugs:
        result = scrape_supermarket.delay(slug)
        task_ids.append(result.id)
        logger.info("Dispatched scrape task for %s (task_id=%s)", slug, result.id)
    return task_ids
