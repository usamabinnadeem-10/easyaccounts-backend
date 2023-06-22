from django.db import models


class RawProductTypes(models.TextChoices):
    BAARA = "Baara", "Baara"
    STANDARD = "Standard", "Standard"


class RawDebitTypes(models.TextChoices):
    SALE = "sale", "Sale"
    PURCHASE_RETURN = "purchase_return", "Purchase Return"
    SALE_RETURN = "sale_return", "Sale Return"


class RawProductGlueTypes(models.TextChoices):
    LG = "low_glue", "Low Glue"
    HG = "high_glue", "High Glue"
    CNT = "centrifugal", "Centrifugal"
