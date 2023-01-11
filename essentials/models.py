from datetime import datetime

from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.db.models import F, Sum

from authentication.models import BranchAwareModel
from core.constants import MIN_POSITIVE_VAL_SMALL
from core.models import ID

from .choices import LinkedAccountChoices, PersonChoices


class ProductCategory(BranchAwareModel):

    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Product Categories"
        verbose_name_plural = "Product Categories"
        unique_together = ["name", "branch"]

    def __str__(self):
        return f"{self.name} - {self.branch.name}"


class Product(ID):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(ProductCategory, on_delete=models.PROTECT)

    class Meta:
        unique_together = ("name", "category")

    def __str__(self) -> str:
        return f"{self.name} - {self.category.branch.name}"


class Area(BranchAwareModel):
    name = models.CharField(max_length=100)
    # city = models.IntegerField()


class Warehouse(BranchAwareModel):
    name = models.CharField(max_length=50)
    # address = models.CharField(max_length=50, null=True)

    def __str__(self) -> str:
        return self.name


class Person(BranchAwareModel):
    """Supplier or Customer Account"""

    name = models.CharField(max_length=100)
    person_type = models.CharField(max_length=3, choices=PersonChoices.choices)
    # business_name = models.CharField(max_length=100, null=True)
    address = models.CharField(max_length=300, null=True, blank=True)
    phone_number = models.CharField(
        max_length=13,
        validators=[
            RegexValidator(
                regex="^\+\d{12}$",
                message="Phone number should look like this (+923001234567)",
                code="nomatch",
            ),
        ],
        null=True,
        blank=True,
    )
    # city = models.IntegerField(null=True)
    area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self) -> str:
        return self.name + ": " + self.person_type

    class Meta:
        unique_together = ("branch", "phone_number")


class AccountType(BranchAwareModel):
    """Account types like cash account or cheque account"""

    name = models.CharField(max_length=100)
    opening_balance = models.FloatField(default=0.0)

    def __str__(self) -> str:
        return f"{self.name} {self.branch.name}"


class Stock(ID):
    """Product stock quantity"""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=False)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, null=False)
    yards_per_piece = models.FloatField(
        validators=[MinValueValidator(MIN_POSITIVE_VAL_SMALL)]
    )
    opening_stock = models.FloatField(default=0.0)
    opening_stock_rate = models.FloatField(default=0.0)

    class Meta:
        unique_together = ("product", "warehouse", "yards_per_piece")

    @classmethod
    def get_total_opening_inventory(cls, branch):
        return (
            Stock.objects.filter(warehouse__branch=branch).aggregate(
                inventory=Sum(
                    F("opening_stock") * F("yards_per_piece") * F("opening_stock_rate")
                )
            )["inventory"]
            or 0
        )


class LinkedAccount(ID):
    name = models.CharField(max_length=15, choices=LinkedAccountChoices.choices)
    account = models.ForeignKey(AccountType, on_delete=models.CASCADE)


class OpeningSaleData(BranchAwareModel):

    date = models.DateTimeField(default=datetime.now)
    revenue = models.FloatField(validators=[MinValueValidator(MIN_POSITIVE_VAL_SMALL)])
    cogs = models.FloatField(validators=[MinValueValidator(MIN_POSITIVE_VAL_SMALL)])
    expense = models.FloatField(validators=[MinValueValidator(MIN_POSITIVE_VAL_SMALL)])

    class Meta:
        verbose_name_plural = "Opening Sales Data"

    @classmethod
    def get_opening_profit(cls, branch, date=None):
        date_filter = {"date__lte": date} if date else {}
        return (
            OpeningSaleData.objects.filter(branch=branch, **date_filter).aggregate(
                total=Sum(F("revenue") - (F("cogs") + F("expense")))
            )["total"]
            or 0
        )

    @classmethod
    def get_opening_sales_data(cls, branch, date=None):
        date_filter = {"date__lte": date} if date else {}
        return OpeningSaleData.objects.filter(branch=branch, **date_filter).aggregate(
            revenue=Sum("revenue"), cogs=Sum("cogs"), expenses=Sum("expense")
        )
