# Bridge file for Celery autodiscovery.
# autodiscover_tasks() looks for <app>/tasks.py, so we re-export from the scrapers subpackage.
from apps.products.scrapers.tasks import scrape_all_supermarkets, scrape_supermarket  # noqa: F401

# Import concrete scraper implementations to trigger @register_scraper decorators.
from products.scrapers.impls import ah, jumbo, lidl  # noqa: F401
