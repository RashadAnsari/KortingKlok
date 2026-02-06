from apps.products.scrapers.base import BaseSupermarketScraper
from apps.products.scrapers.dtos import ScrapedCategory, ScrapedProduct
from apps.products.scrapers.registry import register_scraper


@register_scraper
class JumboScraper(BaseSupermarketScraper):
    supermarket_slug = "jumbo"

    def scrape_categories(self) -> list[ScrapedCategory]:
        raise NotImplementedError

    def scrape_products(self) -> list[ScrapedProduct]:
        raise NotImplementedError
