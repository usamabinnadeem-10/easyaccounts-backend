from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, RegexValidator
from django.contrib.auth.models import User
from uuid import uuid4

from .choices import *


class ID(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)


class Product(ID):
    si_unit = models.CharField(max_length=5, choices=QuantityChoices.choices)
    basic_unit = models.FloatField()
    name = models.CharField(max_length=100, unique=True)

    def __str__(self) -> str:
        return self.name


class Warehouse(ID):
    name = models.CharField(max_length=50)
    address = models.CharField(max_length=50, null=True)

    def __str__(self) -> str:
        return self.name


class Person(ID):
    """Supplier or Customer Account"""

    name = models.CharField(max_length=100, unique=True)
    person_type = models.CharField(max_length=1, choices=PersonChoices.choices)
    business_name = models.CharField(max_length=100, null=True)
    address = models.CharField(max_length=300, null=True)
    phone_number = models.CharField(
        max_length=13,
        validators=[
            RegexValidator(
                regex="^\+\d{12}$",
                message="Phone number should look like this (+923001234567)",
                code="nomatch",
            ),
        ],
        unique=True,
    )
    city = models.CharField(max_length=100, null=True)

    def __str__(self) -> str:
        return self.name + ": " + self.person_type


class AccountType(ID):
    """Account types like cash account or cheque account"""

    name = models.CharField(max_length=100)

    def __str__(self) -> str:
        return self.name


class Stock(models.Model):
    """Product stock quantity"""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=False)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, null=False)
    stock_quantity = models.FloatField(validators=[MinValueValidator(0.0)], default=0.0)
    yards_per_piece = models.FloatField(validators=[MinValueValidator(1.0)])

    class Meta:
        unique_together = ("product", "warehouse", "yards_per_piece")


class LinkedAccount(models.Model):

    name = models.CharField(max_length=100)
    account = models.ForeignKey(AccountType, on_delete=models.CASCADE)


class Branch(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=255)


class UserBranchRelation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    role = models.CharField(
        max_length=20, choices=RoleChoices.choices, default=RoleChoices.ACCOUNTANT
    )
