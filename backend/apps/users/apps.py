from django.apps import AppConfig

import firebase_admin


class UsersConfig(AppConfig):
    name = "users"

    def ready(self):
        try:
            firebase_admin.get_app()
        except ValueError:
            firebase_admin.initialize_app()
