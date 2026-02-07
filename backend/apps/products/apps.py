from django.apps import AppConfig

SUPERMARKETS = [
    (
        "ah",
        "Albert Heijn",
        "https://www.ah.nl",
        "https://upload.wikimedia.org/wikipedia/commons/e/eb/Albert_Heijn_Logo.svg",
    ),
    (
        "jumbo",
        "Jumbo",
        "https://www.jumbo.com",
        "https://upload.wikimedia.org/wikipedia/commons/8/8d/Jumbo_Logo.svg",
    ),
    (
        "lidl",
        "Lidl",
        "https://www.lidl.nl",
        "https://upload.wikimedia.org/wikipedia/commons/9/91/Lidl-Logo.svg",
    ),
]


class ProductsConfig(AppConfig):
    name = "products"

    def ready(self):
        try:
            self._seed_supermarkets()
        except Exception:
            pass

    def _seed_supermarkets(self):
        from products.models import Supermarket

        for slug, name, website_url, logo_url in SUPERMARKETS:
            Supermarket.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "website_url": website_url,
                    "logo_url": logo_url,
                },
            )
