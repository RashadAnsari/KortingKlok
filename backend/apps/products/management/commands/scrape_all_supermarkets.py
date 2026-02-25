from django.core.management.base import BaseCommand

from products.scrapers.impls import ah, jumbo, lidl  # noqa: F401
from products.scrapers.registry import get_all_slugs
from products.scrapers.tasks import scrape_supermarket


class Command(BaseCommand):
    help = "Dispatch scrape tasks for all registered supermarkets."

    def handle(self, *args, **options):
        slugs = get_all_slugs()
        self.stdout.write(f"Dispatching scrape tasks for {len(slugs)} supermarkets...")
        for slug in slugs:
            kwargs = {"queue": "celery-slow"} if slug == "lidl" else {}
            result = scrape_supermarket.apply_async((slug,), **kwargs)
            self.stdout.write(f"  {slug} -> task_id={result.id}")
        self.stdout.write(self.style.SUCCESS(f"Dispatched {len(slugs)} scrape tasks."))
