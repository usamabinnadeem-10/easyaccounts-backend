from django.db import models
from django.core.validators import MinValueValidator
from uuid import uuid4

from essentials.models import AccountType, Warehouse, Product, Person

from datetime import date

from django.db.models import Sum

from .choices import *

from authentication.models import BranchAwareModel


class Transaction(BranchAwareModel):
    date = models.DateField(default=date.today)
    nature = models.CharField(max_length=1, choices=TransactionChoices.choices)
    discount = models.FloatField(validators=[MinValueValidator(0.0)], default=0.0)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    draft = models.BooleanField(default=False)
    type = models.CharField(max_length=10, choices=TransactionTypes.choices)
    serial = models.BigIntegerField()
    detail = models.CharField(max_length=1000, null=True)
    account_type = models.ForeignKey(AccountType, null=True, on_delete=models.SET_NULL)
    paid_amount = models.FloatField(default=0.0)
    manual_invoice_serial = models.BigIntegerField()
    manual_serial_type = models.CharField(max_length=3)
    requires_action = models.BooleanField(default=False)

    class Meta:
        ordering = ["serial"]
        unique_together = ("manual_invoice_serial", "manual_serial_type", "branch")


class TransactionDetail(BranchAwareModel):
    transaction = models.ForeignKey(
        Transaction, on_delete=models.CASCADE, related_name="transaction_detail"
    )
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, null=True, name="product"
    )
    rate = models.FloatField(validators=[MinValueValidator(0.0)])
    yards_per_piece = models.FloatField(validators=[MinValueValidator(1.0)])
    quantity = models.FloatField(validators=[MinValueValidator(1.0)])
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True)
    amount = models.FloatField(validators=[MinValueValidator(0.0)])


class CancelledInvoice(BranchAwareModel):
    manual_invoice_serial = models.BigIntegerField()
    manual_serial_type = models.CharField(max_length=3)
    comment = models.CharField(max_length=500)

    class Meta:
        unique_together = ("manual_invoice_serial", "manual_serial_type", "branch")


class TransferEntry(BranchAwareModel):
    date = models.DateField(default=date.today)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    yards_per_piece = models.FloatField(validators=[MinValueValidator(0.0)])
    from_warehouse = models.ForeignKey(
        Warehouse, on_delete=models.CASCADE, related_name="from_warehouse"
    )
    to_warehouse = models.ForeignKey(
        Warehouse, on_delete=models.CASCADE, related_name="to_warehouse"
    )
    quantity = models.FloatField(validators=[MinValueValidator(0.0)])

    class Meta:
        verbose_name_plural = "Transfer entries"

    @classmethod
    def calculateTransferredAmount(cls, warehouse, product, filters):
        custom_filters = {
            **filters,
            "product": product,
        }
        values = ["product", "from_warehouse", "to_warehouse"]
        quantity = 0.0
        transfers_in = (
            TransferEntry.objects.values(*values)
            .annotate(quantity=Sum("quantity"))
            .filter(
                **{
                    **custom_filters,
                    "to_warehouse": warehouse,
                }
            )
        )
        for t in transfers_in:
            quantity += t["quantity"]

        transfers_out = (
            TransferEntry.objects.values(*values)
            .annotate(quantity=Sum("quantity"))
            .filter(
                **{
                    **custom_filters,
                    "from_warehouse": warehouse,
                }
            )
        )

        for t in transfers_out:
            quantity -= t["quantity"]

        return quantity
