from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from uuid import uuid4

from essentials.models import AccountType, Warehouse, Product, Person

from datetime import date

from django.db.models import Sum


class TransactionChoices(models.TextChoices):
    CREDIT = "C", _("Credit")
    DEBIT = "D", _("Debit")


class TransactionTypes(models.TextChoices):
    MAAL_WAPSI = "maal_wapsi", _("Maal Wapsi")
    PAID = "paid", _("Paid")
    PURCHASE = "purchase", _("Purchase")
    CREDIT = "credit", _("Credit")


class Transaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    date = models.DateField(default=date.today)
    nature = models.CharField(max_length=1, choices=TransactionChoices.choices)
    discount = models.FloatField(validators=[MinValueValidator(0.0)], default=0.0)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    draft = models.BooleanField(default=False)
    type = models.CharField(max_length=10, choices=TransactionTypes.choices)
    serial = models.BigIntegerField(unique=True)
    detail = models.CharField(max_length=1000, null=True)
    account_type = models.ForeignKey(AccountType, null=True, on_delete=models.SET_NULL)
    paid_amount = models.FloatField(default=0.0)
    manual_invoice_serial = models.BigIntegerField()
    manual_serial_type = models.CharField(max_length=3)

    class Meta:
        ordering = ["-date", "-serial"]
        unique_together = ("manual_invoice_serial", "manual_serial_type")


class TransactionDetail(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    transaction = models.ForeignKey(
        Transaction, on_delete=models.CASCADE, related_name="transaction_detail"
    )
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, null=True, name="product"
    )
    rate = models.FloatField(validators=[MinValueValidator(0.0)])
    yards_per_piece = models.FloatField(validators=[MinValueValidator(1.0)])
    quantity = models.FloatField(validators=[MinValueValidator(1.0)])
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True)
    amount = models.FloatField(validators=[MinValueValidator(0.0)])


class CancelledInvoice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    manual_invoice_serial = models.BigIntegerField(unique=True)
    manual_serial_type = models.CharField(max_length=3)
    comment = models.CharField(max_length=500)

    class Meta:
        unique_together = ("manual_invoice_serial", "manual_serial_type")


class TransferEntry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
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
