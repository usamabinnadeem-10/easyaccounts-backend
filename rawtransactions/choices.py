from django.db import models


class RawProductTypes(models.TextChoices):
    BAARA = "Baara", "Baara"
    STANDARD = "Standard", "Standard"


class RawDebitTypes(models.TextChoices):
    SALE = "sale", "Sale"
    PURCHASE_RETURN = "purchase_return", "Purchase Return"
    SALE_RETURN = "sale_return", "Sale Return"


class RawProductGlueTypes(models.TextChoices):
    LG = "LG", "Low Glue"
    HG = "HG", "High Glue"
    CNT = "CFG", "Centrifugal"
