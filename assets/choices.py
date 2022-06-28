from django.db import models

PURCHASED = "P"
SOLD = "S"


class AssetStatusChoices(models.TextChoices):
    PURCHASED = PURCHASED, "Purchased"
    SOLD = SOLD, "Sold"


class AssetTypeChoices(models.TextChoices):
    PROPERTY = "property", "Property"
    EQUIPMENT = "equipment", "Equipment"
    INVESTMENT = "investment", "Investment"
    VEHICLE = "vehicle", "Vehicle"
