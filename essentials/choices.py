from django.db import models


class QuantityChoices(models.TextChoices):
    YARDS = "yards", "Yards"
    PIECE = "piece", "Pieces"


SUPPLIER = "S"
CUSTOMER = "C"


class PersonChoices(models.TextChoices):
    SUPPLIER = SUPPLIER, "Supplier"
    CUSTOMER = CUSTOMER, "Customer"


class RoleChoices(models.TextChoices):
    ACCOUNTANT = "accountant", "Accountant"
    ADMIN = "admin", "Admin"
