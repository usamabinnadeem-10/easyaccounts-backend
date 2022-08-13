from django.db import models


class RawProductTypes(models.TextChoices):
    BAARA = "Baara", "Baara"
    STANDARD = "Standard", "Standard"


class RawSaleAndReturnTypes(models.TextChoices):
    RINV = "RINV", "Raw Sale"
    RMWC = "RMWC", "Return Customer"
    RMWS = "RMWS", "Return Supplier"
