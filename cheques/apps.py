from django.apps import AppConfig


class ChequesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "cheques"

    def ready(self):
        import cheques.signals
