from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class ScrapedCategory:
    """A category as scraped from a supermarket source."""

    external_id: str
    name: str
    parent_external_id: str | None = None


@dataclass(frozen=True, slots=True)
class ScrapedProduct:
    """A product as scraped from a supermarket source.

    All price fields use Decimal to avoid floating-point issues.
    """

    external_id: str
    name: str
    base_price: Decimal | None = None
    current_price: Decimal | None = None
    has_discount: bool = False
    discount_text: str | None = None
    image_url: str | None = None
    website_url: str | None = None
    category_external_id: str | None = None
