from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from uuid import uuid4


class ID(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)


class QuantityChoices(models.TextChoices):
    YARDS = "yards", _("Yards")
    PIECE = "piece", _("Pieces")


class Product(ID):
    si_unit = models.CharField(max_length=5, choices=QuantityChoices.choices)
    basic_unit = models.FloatField()
    name = models.CharField(max_length=100)

    def __str__(self) -> str:
        return self.name


class Warehouse(ID):
    name = models.CharField(max_length=50)
    address = models.CharField(max_length=50, null=True)

    def __str__(self) -> str:
        return self.name


SUPPLIER = "S"
CUSTOMER = "C"


class PersonChoices(models.TextChoices):
    SUPPLIER = SUPPLIER, _("Supplier")
    CUSTOMER = CUSTOMER, _("Customer")


class Person(ID):
    """Supplier or Customer Account"""
    name = models.CharField(max_length=100)
    person_type = models.CharField(max_length=1, choices=PersonChoices.choices)
    business_name = models.CharField(max_length=100, null=True)

    def __str__(self) -> str:
        return self.name + ": " + self.person_type


"""Account types like cash account or cheque account"""


class AccountType(ID):
    name = models.CharField(max_length=100)

    def __str__(self) -> str:
        return self.name


class Stock(models.Model):
    """Product stock quantity"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=False)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, null=False)
    stock_quantity = models.FloatField(validators=[MinValueValidator(0.0)], default=0.0)

    class Meta:
        unique_together = ('product', 'warehouse')