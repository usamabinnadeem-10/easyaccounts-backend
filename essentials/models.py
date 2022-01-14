from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from uuid import uuid4



class ID(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)


class ProductColor(ID):
    color_name = models.CharField(max_length=50)

    def __str__(self) -> str:
        return self.color_name


class ProductHead(ID):
    head_name = models.CharField(max_length=50)

    def __str__(self) -> str:
        return self.head_name


class QuantityChoices(models.TextChoices):
    YARDS = "yards", _("Yards")
    PIECE = "piece", _("Pieces")


class Product(ID):
    si_unit = models.CharField(max_length=5, choices=QuantityChoices.choices)
    basic_unit = models.FloatField()
    product_head = models.ForeignKey(ProductHead, on_delete=models.CASCADE)
    product_color = models.ForeignKey(ProductColor, on_delete=models.CASCADE, null=True)
    stock_quantity = models.FloatField(validators=[MinValueValidator(0.0)])

    def __str__(self) -> str:
        return self.product_head.head_name + ": " + self.product_color.color_name

    class Meta:
        unique_together = ('product_head', 'product_color')


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


"""Supplier or Customer Account"""


class Person(ID):
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
