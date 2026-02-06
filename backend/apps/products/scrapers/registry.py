from apps.products.scrapers.base import BaseSupermarketScraper

_REGISTRY: dict[str, type[BaseSupermarketScraper]] = {}


def register_scraper(scraper_class: type[BaseSupermarketScraper]) -> type[BaseSupermarketScraper]:
    """Class decorator to register a scraper in the global registry.

    Usage:
        @register_scraper
        class AlbertHeijnScraper(BaseSupermarketScraper):
            supermarket_slug = "ah"
            ...
    """
    slug = scraper_class.supermarket_slug
    if slug in _REGISTRY:
        raise ValueError(f"Scraper already registered for slug '{slug}'")
    _REGISTRY[slug] = scraper_class
    return scraper_class


def get_scraper(slug: str) -> BaseSupermarketScraper:
    """Instantiate and return the scraper for the given supermarket slug."""
    if slug not in _REGISTRY:
        available = ", ".join(sorted(_REGISTRY.keys())) or "(none)"
        raise ValueError(f"No scraper registered for slug '{slug}'. Available: {available}")
    return _REGISTRY[slug]()


def get_all_slugs() -> list[str]:
    """Return all registered supermarket slugs."""
    return list(_REGISTRY.keys())
