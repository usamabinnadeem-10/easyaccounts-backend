from django.db import models


class RawProductTypes(models.TextChoices):
    BAARA = "Baara", "Baara"
    STANDARD = "Standard", "Standard"


class RawDebitTypes(models.TextChoices):
    SALE = "Sale", "Sale"
    RETURN = "Return", "Return"
