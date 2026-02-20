from django.core.management.base import BaseCommand

from products.scrapers.impls import ah, jumbo, lidl  # noqa: F401
from products.scrapers.registry import get_all_slugs
from products.scrapers.tasks import scrape_supermarket


class Command(BaseCommand):
    help = "Dispatch scrape tasks for all registered supermarkets."

    def handle(self, *args, **options):
        slugs = get_all_slugs()
        self.stdout.write(f"Dispatching scrape tasks for {len(slugs)} supermarkets...")
        for i, slug in enumerate(slugs):
            delay_seconds = i * 30 * 60  # 0 min, 30 min, 60 min, …
            result = scrape_supermarket.apply_async((slug,), countdown=delay_seconds)
            self.stdout.write(f"  {slug} -> task_id={result.id} (in {delay_seconds // 60} min)")
        self.stdout.write(self.style.SUCCESS(f"Dispatched {len(slugs)} scrape tasks."))
