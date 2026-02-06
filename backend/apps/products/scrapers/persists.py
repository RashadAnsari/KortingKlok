import logging
import uuid

from apps.products.models import Category, PriceHistory, Product, Supermarket
from apps.products.scrapers.dtos import ScrapedCategory, ScrapedProduct

logger = logging.getLogger("scrapers.persists")


def get_supermarket(slug: str) -> Supermarket:
    """Retrieve the Supermarket record by slug. Raises DoesNotExist if not found."""
    return Supermarket.objects.get(slug=slug)


def sync_categories(
    supermarket: Supermarket,
    scraped_categories: list[ScrapedCategory],
) -> dict[str, Category]:
    """Sync scraped categories into the database.

    Uses update_or_create keyed on (supermarket, external_id).
    Two-pass approach: first create/update all categories, then set parent
    relationships (since parents might appear after children in the list).

    Returns a dict mapping external_id -> Category instance.
    """
    category_map: dict[str, Category] = {}

    for sc in scraped_categories:
        category, created = Category.objects.update_or_create(
            supermarket=supermarket,
            external_id=sc.external_id,
            defaults={"name": sc.name},
        )
        category_map[sc.external_id] = category
        logger.debug("%s category %s (external_id=%s)", "Created" if created else "Updated", sc.name, sc.external_id)

    # Second pass: set parent relationships
    for sc in scraped_categories:
        if sc.parent_external_id and sc.parent_external_id in category_map:
            category = category_map[sc.external_id]
            parent = category_map[sc.parent_external_id]
            if category.parent_id != parent.id:
                category.update(parent=parent)

    logger.info("Synced %d categories for %s", len(scraped_categories), supermarket.slug)
    return category_map


def _has_price_changed(product: Product, scraped: ScrapedProduct) -> bool:
    """Check whether any price-related field has changed."""
    return (
        product.base_price != scraped.base_price
        or product.current_price != scraped.current_price
        or product.has_discount != scraped.has_discount
        or product.discount_text != scraped.discount_text
    )


def _create_price_history(product: Product, run_id: uuid.UUID) -> None:
    """Create a PriceHistory snapshot from the product's current state."""
    PriceHistory.objects.create(
        product=product,
        base_price=product.base_price,
        price=product.current_price,
        has_discount=product.has_discount,
        discount_text=product.discount_text,
        run_id=run_id,
    )


def sync_products(
    supermarket: Supermarket,
    scraped_products: list[ScrapedProduct],
    category_map: dict[str, Category] | None = None,
    *,
    run_id: uuid.UUID,
) -> dict:
    """Sync scraped products into the database.

    For each product: update-or-create by (supermarket, external_id).
    Updates ALL product fields (name, image, url, prices, etc.) on every sync.
    Creates PriceHistory entries when prices change or for new products.
    Marks products not in the scraped list as unavailable.

    Returns stats: {created, updated, price_changes, marked_unavailable}.
    """
    stats = {"created": 0, "updated": 0, "price_changes": 0, "marked_unavailable": 0}
    seen_external_ids: set[str] = set()

    for sp in scraped_products:
        seen_external_ids.add(sp.external_id)

        category = None
        if category_map and sp.category_external_id:
            category = category_map.get(sp.category_external_id)

        defaults = {
            "name": sp.name,
            "base_price": sp.base_price,
            "current_price": sp.current_price,
            "has_discount": sp.has_discount,
            "discount_text": sp.discount_text,
            "image_url": sp.image_url,
            "website_url": sp.website_url,
            "category": category,
            "is_available": True,
        }

        try:
            product = Product.objects.get(supermarket=supermarket, external_id=sp.external_id)
            price_changed = _has_price_changed(product, sp)
            product.update(**defaults)

            if price_changed:
                _create_price_history(product, run_id=run_id)
                stats["price_changes"] += 1

            stats["updated"] += 1
        except Product.DoesNotExist:
            product = Product.objects.create(supermarket=supermarket, external_id=sp.external_id, **defaults)
            _create_price_history(product, run_id=run_id)
            stats["created"] += 1
            stats["price_changes"] += 1

    # Mark unseen products as unavailable
    stats["marked_unavailable"] = (
        Product.objects.filter(supermarket=supermarket, is_available=True)
        .exclude(external_id__in=seen_external_ids)
        .update(is_available=False)
    )

    logger.info(
        "Synced products for %s: created=%d, updated=%d, price_changes=%d, marked_unavailable=%d",
        supermarket.slug,
        stats["created"],
        stats["updated"],
        stats["price_changes"],
        stats["marked_unavailable"],
    )
    return stats
