from datetime import date

from authentication.models import BranchAwareModel, UserAwareModel
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum
from essentials.models import AccountType, Person, Product, Warehouse
from rawtransactions.models import NextSerial

from .choices import TransactionChoices, TransactionSerialTypes, TransactionTypes


class Transaction(BranchAwareModel, UserAwareModel, NextSerial):
    date = models.DateField(default=date.today)
    nature = models.CharField(max_length=1, choices=TransactionChoices.choices)
    discount = models.FloatField(validators=[MinValueValidator(0.0)], default=0.0)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    draft = models.BooleanField(default=False)
    type = models.CharField(max_length=10, choices=TransactionTypes.choices)
    serial = models.PositiveBigIntegerField()
    detail = models.CharField(max_length=1000, null=True)
    account_type = models.ForeignKey(AccountType, null=True, on_delete=models.SET_NULL)
    paid_amount = models.FloatField(default=0.0)
    manual_invoice_serial = models.BigIntegerField()
    manual_serial_type = models.CharField(
        max_length=3, choices=TransactionSerialTypes.choices
    )
    requires_action = models.BooleanField(default=False)

    class Meta:
        ordering = ["serial"]
        unique_together = (
            "manual_invoice_serial",
            "manual_serial_type",
            "branch",
        )


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

    @classmethod
    def is_rate_invalid(cls, nature, product, current_rate):
        if nature == TransactionChoices.DEBIT:
            return product.minimum_rate > current_rate
        return False


class CancelledInvoice(BranchAwareModel, NextSerial):
    manual_invoice_serial = models.BigIntegerField()
    manual_serial_type = models.CharField(
        max_length=3, choices=TransactionSerialTypes.choices
    )
    comment = models.CharField(max_length=500)

    class Meta:
        unique_together = (
            "manual_invoice_serial",
            "manual_serial_type",
            "branch",
        )


class CancelStockTransfer(BranchAwareModel, NextSerial):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    manual_invoice_serial = models.PositiveBigIntegerField()


class StockTransfer(BranchAwareModel, UserAwareModel, NextSerial):
    date = models.DateField(default=date.today)
    serial = models.PositiveBigIntegerField()
    manual_invoice_serial = models.PositiveBigIntegerField()
    from_warehouse = models.ForeignKey(
        Warehouse, on_delete=models.CASCADE, related_name="from_warehouse", default=None
    )

    class Meta:
        unique_together = ["serial", "manual_invoice_serial", "from_warehouse"]

    class Meta:
        verbose_name_plural = "Stock transfers"


class StockTransferDetail(BranchAwareModel):

    transfer = models.ForeignKey(
        StockTransfer, on_delete=models.CASCADE, related_name="transfer_detail"
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    yards_per_piece = models.FloatField(validators=[MinValueValidator(0.0)])
    to_warehouse = models.ForeignKey(
        Warehouse, on_delete=models.CASCADE, related_name="to_warehouse"
    )
    quantity = models.FloatField(validators=[MinValueValidator(0.0)])

    @classmethod
    def calculateTransferredAmount(cls, warehouse, product, filters):
        """return transferred amount to this warehouse"""
        custom_filters = {
            **filters,
            "product": product,
        }
        values = ["product", "from_warehouse", "to_warehouse"]
        quantity = 0.0
        transfers_in = (
            StockTransferDetail.objects.values(*values)
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

        values[1] = "transfer__from_warehouse"
        transfers_out = (
            StockTransferDetail.objects.values(*values)
            .annotate(quantity=Sum("quantity"))
            .filter(
                **{
                    **custom_filters,
                    "transfer__from_warehouse": warehouse,
                }
            )
        )

        for t in transfers_out:
            quantity -= t["quantity"]

        return quantity
