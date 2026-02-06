# Bridge file for Celery autodiscovery.
# autodiscover_tasks() looks for <app>/tasks.py, so we re-export from subpackages.
from products.notifications.tasks import notify_price_changes, notify_user_price_change  # noqa: F401

# Import concrete scraper implementations to trigger @register_scraper decorators.
from products.scrapers.impls import ah, jumbo, lidl  # noqa: F401
from products.scrapers.tasks import scrape_all_supermarkets, scrape_supermarket  # noqa: F401
