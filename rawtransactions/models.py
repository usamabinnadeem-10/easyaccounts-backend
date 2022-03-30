from datetime import date

from authentication.models import BranchAwareModel
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Max
from essentials.models import Person, Warehouse

from .choices import RawDebitTypes, RawProductTypes


class Formula(BranchAwareModel):

    numerator = models.FloatField()
    denominator = models.FloatField()

    def __str__(self):
        return f"{self.numerator}/{self.denominator}"


class RawProduct(BranchAwareModel):

    name = models.CharField(max_length=100)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    type = models.CharField(max_length=10, choices=RawProductTypes.choices)

    class Meta:
        unique_together = ("person", "name", "branch", "type")

    def __str__(self):
        return f"{self.name} - {self.person} - {self.type}"


class RawProductOpeningStock(BranchAwareModel):

    product = models.ForeignKey(RawProduct, on_delete=models.CASCADE)
    opening_stock = models.FloatField(default=0.0)
    opening_stock_rate = models.FloatField()
    gazaana = models.FloatField()

    class Meta:
        unique_together = ("product", "gazaana", "branch")


class RawTransaction(BranchAwareModel):

    person = models.ForeignKey(Person, on_delete=models.CASCADE, null=True)
    date = models.DateField(default=date.today)
    manual_invoice_serial = models.PositiveBigIntegerField()

    class Meta:
        unique_together = ("manual_invoice_serial", "branch")

    def __str__(self):
        return f"{self.manual_invoice_serial} - {self.person}"


class NextSerial:
    @classmethod
    def get_next_serial(cls, branch, field, **kwargs):
        return (
            cls.objects.filter(branch=branch, **kwargs).aggregate(max_serial=Max(field))[
                "max_serial"
            ]
            or 0
        ) + 1


class RawTransactionLot(BranchAwareModel, NextSerial):

    raw_transaction = models.ForeignKey(RawTransaction, on_delete=models.CASCADE)
    raw_product = models.ForeignKey(RawProduct, on_delete=models.PROTECT)
    lot_number = models.PositiveBigIntegerField()
    issued = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.raw_transaction} - {self.lot_number}"


class AbstractRawLotDetail(BranchAwareModel):

    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1.0)])
    actual_gazaana = models.FloatField(validators=[MinValueValidator(1.0)])
    expected_gazaana = models.FloatField(validators=[MinValueValidator(1.0)])
    rate = models.FloatField(validators=[MinValueValidator(1.0)])
    formula = models.ForeignKey(Formula, on_delete=models.PROTECT)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, null=True)

    class Meta:
        abstract = True


class RawLotDetail(AbstractRawLotDetail):

    lot_number = models.ForeignKey(RawTransactionLot, on_delete=models.CASCADE)


class RawDebit(BranchAwareModel, NextSerial):

    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    manual_invoice_serial = models.PositiveBigIntegerField()
    bill_number = models.PositiveBigIntegerField()
    date = models.DateField(default=date.today)
    debit_type = models.CharField(max_length=10, choices=RawDebitTypes.choices)

    @classmethod
    def is_serial_unique(cls, **kwargs):
        return not RawDebit.objects.filter(**kwargs).exists()

    class Meta:
        unique_together = ("manual_invoice_serial", "branch", "debit_type")


class RawDebitLot(BranchAwareModel):

    bill_number = models.ForeignKey(RawDebit, on_delete=models.CASCADE)
    lot_number = models.ForeignKey(RawTransactionLot, on_delete=models.CASCADE)


class RawDebitLotDetail(AbstractRawLotDetail):

    return_lot = models.ForeignKey(RawDebitLot, on_delete=models.CASCADE)
