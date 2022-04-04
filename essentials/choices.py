from django.db import models

SUPPLIER = "S"
CUSTOMER = "C"


class PersonChoices(models.TextChoices):
    SUPPLIER = SUPPLIER, "Supplier"
    CUSTOMER = CUSTOMER, "Customer"


class ProductCategoryChoices(models.TextChoices):
    CRK = "CRK", "CRK"
    AK = (
        "AK",
        "AK",
    )
    DMD = (
        "DMD",
        "DMD",
    )
    KS = (
        "KS",
        "KS",
    )
