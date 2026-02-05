from django.apps import AppConfig


class UtilsConfig(AppConfig):
    name = "utils"

    def ready(self):
        import utils.schemas  # noqa: F401
