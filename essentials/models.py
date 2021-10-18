from django.db import models
from django.utils.translation import gettext_lazy as _
from uuid import uuid4


class ProductColor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    color_name = models.CharField(max_length=50)

    def __str__(self) -> str:
        return self.color_name


class ProductHead(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    head_name = models.CharField(max_length=50)

    def __str__(self) -> str:
        return self.head_name


class QuantityChoices(models.TextChoices):
    CREDIT = "yards", _("Yards")
    DEBIT = "piece", _("Pieces")


class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    unit = models.CharField(max_length=5, choices=QuantityChoices.choices)
    current_quantity = models.FloatField(default=0.0)
    product_head = models.ForeignKey(ProductHead, on_delete=models.CASCADE)
    product_color = models.ForeignKey(ProductColor, on_delete=models.CASCADE, null=True)

    def __str__(self) -> str:
        return self.product_head.head_name + ": " + self.product_color.color_name


class Warehouse(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=50)
    address = models.CharField(max_length=50, null=True)

    def __str__(self) -> str:
        return self.name


class PersonChoices(models.TextChoices):
    CREDIT = "S", _("Supplier")
    DEBIT = "C", _("Customer")


"""Supplier or Customer Account"""


class Person(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=100)
    person_type = models.CharField(max_length=1, choices=PersonChoices.choices)
    business_name = models.CharField(max_length=100, null=True)

    def __str__(self) -> str:
        return self.name + ": " + self.person_type


"""Account types like cash account or cheque account"""


class AccountType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=100)
    balance = models.FloatField(default=0.0)

    def __str__(self) -> str:
        return self.name
