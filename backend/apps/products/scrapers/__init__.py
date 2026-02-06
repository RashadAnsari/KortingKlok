from apps.products.scrapers.base import BaseSupermarketScraper
from apps.products.scrapers.dtos import ScrapedCategory, ScrapedProduct
from apps.products.scrapers.registry import get_scraper, register_scraper

__all__ = [
    "BaseSupermarketScraper",
    "ScrapedCategory",
    "ScrapedProduct",
    "get_scraper",
    "register_scraper",
]
