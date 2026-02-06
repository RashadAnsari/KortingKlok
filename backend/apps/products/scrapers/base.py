import logging
from abc import ABC, abstractmethod

from products.scrapers.dtos import ScrapedCategory, ScrapedProduct


class BaseSupermarketScraper(ABC):
    """Abstract base class for supermarket scrapers.

    Each supermarket (Albert Heijn, Jumbo, Lidl, etc.) implements this interface.
    The scraper is responsible ONLY for fetching and parsing data from the external
    source into plain dataclasses. DB persistence is handled separately by the
    persists module.

    Subclasses MUST set `supermarket_slug` as a class attribute matching the
    corresponding Supermarket.slug in the database.

    Usage:
        scraper = AlbertHeijnScraper()
        categories = scraper.scrape_categories()
        products = scraper.scrape_products()
    """

    supermarket_slug: str

    def __init__(self):
        self.logger = logging.getLogger(f"scrapers.{self.supermarket_slug}")

    @abstractmethod
    def scrape_categories(self) -> list[ScrapedCategory]:
        """Fetch and return all categories from the supermarket.

        Returns a full snapshot of categories. Implementations should handle
        pagination and any API-specific logic internally.
        """
        ...

    @abstractmethod
    def scrape_products(self) -> list[ScrapedProduct]:
        """Fetch and return all products from the supermarket.

        Returns a full snapshot of products. Products not present in this list
        will be marked as unavailable during sync. Implementations should handle
        pagination internally.
        """
        ...

    def close(self) -> None:
        """Clean up resources. Called after scraping is complete."""
