from django.db import models

from .choices import RawProductTypes
from essentials.models import Person, Warehouse
from authentication.models import BranchAwareModel
from transactions.choices import TransactionChoices

from datetime import date


class Formula(BranchAwareModel):

    numerator = models.FloatField()
    denominator = models.FloatField()


class RawProduct(BranchAwareModel):

    name = models.CharField(max_length=100)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    type = models.CharField(max_length=10, choices=RawProductTypes.choices)


class RawProductOpeningStock(BranchAwareModel):

    product = models.ForeignKey(RawProduct, on_delete=models.CASCADE)
    opening_stock = models.FloatField(default=0.0)
    opening_stock_rate = models.FloatField()
    gazaana = models.FloatField()


class RawTransaction(BranchAwareModel):

    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    date = models.DateField(default=date.today)
    manual_invoice_serial = models.PositiveBigIntegerField()
    nature = models.CharField(max_length=1, choices=TransactionChoices.choices)


class RawTransactionLot(BranchAwareModel):

    raw_transaction = models.ForeignKey(RawTransaction, on_delete=models.CASCADE)
    lot_number = models.PositiveBigIntegerField()
    issued = models.BooleanField(default=False)


class RawLotDetails(BranchAwareModel):

    lot_number = models.ForeignKey(RawTransactionLot, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    actual_gazaana = models.FloatField()
    expected_gazaana = models.FloatField()
    formula = models.ForeignKey(Formula, on_delete=models.PROTECT)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
