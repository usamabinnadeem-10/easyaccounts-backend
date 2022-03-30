from django.apps import AppConfig


class RawtransactionsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "rawtransactions"

    def ready(self):
        import rawtransactions.signals
