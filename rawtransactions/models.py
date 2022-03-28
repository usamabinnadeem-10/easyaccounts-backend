from datetime import date

from authentication.models import BranchAwareModel
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Max
from essentials.models import Person, Warehouse
from transactions.choices import TransactionChoices

from .choices import RawProductTypes


class Formula(BranchAwareModel):

    numerator = models.FloatField()
    denominator = models.FloatField()


class RawProduct(BranchAwareModel):

    name = models.CharField(max_length=100)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    type = models.CharField(max_length=10, choices=RawProductTypes.choices)

    class Meta:
        unique_together = ("person", "name", "branch", "type")


class RawProductOpeningStock(BranchAwareModel):

    product = models.ForeignKey(RawProduct, on_delete=models.CASCADE)
    opening_stock = models.FloatField(default=0.0)
    opening_stock_rate = models.FloatField()
    gazaana = models.FloatField()


class RawTransaction(BranchAwareModel):

    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    date = models.DateField(default=date.today)
    manual_invoice_serial = models.PositiveBigIntegerField()


class RawTransactionLot(BranchAwareModel):

    raw_transaction = models.ForeignKey(RawTransaction, on_delete=models.CASCADE)
    raw_product = models.ForeignKey(RawProduct, on_delete=models.PROTECT)
    lot_number = models.PositiveBigIntegerField()
    issued = models.BooleanField(default=False)

    @classmethod
    def get_next_serial(cls, branch):
        return (
            RawTransactionLot.objects.filter(branch=branch).aggregate(
                max_lot=Max("lot_number")
            )["max_lot"]
            or 0
        ) + 1


class RawLotDetail(BranchAwareModel):

    lot_number = models.ForeignKey(RawTransactionLot, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    actual_gazaana = models.FloatField()
    expected_gazaana = models.FloatField()
    rate = models.FloatField(validators=[MinValueValidator(0.0)])
    formula = models.ForeignKey(Formula, on_delete=models.PROTECT)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, null=True)
    nature = models.CharField(
        max_length=1,
        choices=TransactionChoices.choices,
        default=TransactionChoices.CREDIT,
    )
