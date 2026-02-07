from products.scrapers.base import BaseSupermarketScraper
from products.scrapers.dtos import ScrapedCategory, ScrapedProduct
from products.scrapers.registry import register_scraper


# @register_scraper
class LidlScraper(BaseSupermarketScraper):
    supermarket_slug = "lidl"

    def scrape_categories(self) -> list[ScrapedCategory]:
        raise NotImplementedError

    def scrape_products(self) -> list[ScrapedProduct]:
        raise NotImplementedError
