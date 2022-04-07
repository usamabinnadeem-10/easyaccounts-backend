from uuid import uuid4

from authentication.models import BranchAwareModel
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

from .choices import PersonChoices


class ProductCategory(BranchAwareModel):

    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Product Categories"
        verbose_name_plural = "Product Categories"
        unique_together = ["name", "branch"]

    def __str__(self):
        return self.name


class Product(BranchAwareModel):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(ProductCategory, on_delete=models.PROTECT)
    minimum_rate = models.FloatField(validators=[MinValueValidator(1.0)], default=1.0)

    class Meta:
        unique_together = ("name", "category", "branch")

    def __str__(self) -> str:
        return self.name


class Area(BranchAwareModel):
    name = models.CharField(max_length=100)
    city = models.IntegerField()


class Warehouse(BranchAwareModel):
    name = models.CharField(max_length=50)
    address = models.CharField(max_length=50, null=True)

    def __str__(self) -> str:
        return self.name


class Person(BranchAwareModel):
    """Supplier or Customer Account"""

    name = models.CharField(max_length=100)
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
        null=True,
    )
    city = models.IntegerField(null=True)
    area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True)
    opening_balance = models.FloatField(default=0.0)

    class Meta:
        unique_together = ("name", "branch")

    def __str__(self) -> str:
        return self.name + ": " + self.person_type


class AccountType(BranchAwareModel):
    """Account types like cash account or cheque account"""

    name = models.CharField(max_length=100)
    opening_balance = models.FloatField(default=0.0)

    def __str__(self) -> str:
        return f"{self.name} {self.branch.name}"


class Stock(BranchAwareModel):
    """Product stock quantity"""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=False)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, null=False)
    stock_quantity = models.FloatField(validators=[MinValueValidator(0.0)], default=0.0)
    yards_per_piece = models.FloatField(validators=[MinValueValidator(1.0)])
    opening_stock = models.FloatField(default=0.0)
    opening_stock_rate = models.FloatField(default=0.0)

    class Meta:
        unique_together = ("product", "warehouse", "yards_per_piece", "branch")


class LinkedAccount(BranchAwareModel):
    name = models.CharField(max_length=100)
    account = models.ForeignKey(AccountType, on_delete=models.CASCADE)
