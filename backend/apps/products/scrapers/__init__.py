from products.scrapers.base import BaseSupermarketScraper
from products.scrapers.dtos import ScrapedCategory, ScrapedProduct
from products.scrapers.registry import get_scraper, register_scraper

__all__ = [
    "BaseSupermarketScraper",
    "ScrapedCategory",
    "ScrapedProduct",
    "get_scraper",
    "register_scraper",
]
