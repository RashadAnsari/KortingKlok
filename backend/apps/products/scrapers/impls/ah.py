from products.scrapers.base import BaseSupermarketScraper
from products.scrapers.dtos import ScrapedCategory, ScrapedProduct
from products.scrapers.registry import register_scraper


@register_scraper
class AlbertHeijnScraper(BaseSupermarketScraper):
    supermarket_slug = "ah"

    def scrape_categories(self) -> list[ScrapedCategory]:
        raise NotImplementedError

    def scrape_products(self) -> list[ScrapedProduct]:
        raise NotImplementedError
