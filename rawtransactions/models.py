from authentication.models import BranchAwareModel, UserAwareModel
from core.constants import MIN_POSITIVE_VAL_SMALL
from core.models import ID, DateTimeAwareModel, NextSerial
from django.core.validators import MinValueValidator
from django.db import models
from essentials.models import Person, Warehouse
from transactions.choices import TransactionChoices

from .choices import RawProductTypes, RawSaleAndReturnTypes


class Formula(BranchAwareModel):
    """Raw product formulas"""

    numerator = models.FloatField()
    denominator = models.FloatField()

    def __str__(self):
        return f"{self.numerator}/{self.denominator}"


class AbstractRawLotDetail(ID):

    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(MIN_POSITIVE_VAL_SMALL)]
    )
    actual_gazaana = models.FloatField(validators=[MinValueValidator(1.0)])
    expected_gazaana = models.FloatField(validators=[MinValueValidator(1.0)])
    rate = models.FloatField(validators=[MinValueValidator(1.0)])
    formula = models.ForeignKey(Formula, on_delete=models.PROTECT)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, null=True)

    class Meta:
        abstract = True


class RawProduct(ID):
    """Raw product"""

    name = models.CharField(max_length=100)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    type = models.CharField(max_length=10, choices=RawProductTypes.choices)

    class Meta:
        unique_together = ("person", "name", "type")

    def __str__(self):
        return f"{self.name} - {self.person} - {self.type}"


class RawPurchase(ID, UserAwareModel, NextSerial, DateTimeAwareModel):
    """Raw transaction"""

    person = models.ForeignKey(Person, on_delete=models.CASCADE, null=True)
    manual_serial = models.PositiveBigIntegerField()
    serial = models.PositiveBigIntegerField()

    def __str__(self):
        return f"{self.serial} - {self.person}"


class RawPurchaseLot(ID, NextSerial):
    """Lot for raw transaction"""

    raw_purchase = models.ForeignKey(
        RawPurchase, on_delete=models.CASCADE, related_name="raw_purchase_transaction"
    )
    raw_product = models.ForeignKey(RawProduct, on_delete=models.PROTECT)
    lot_number = models.PositiveBigIntegerField()
    issued = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.raw_purchase} - {self.lot_number}"


class RawPurchaseLotDetail(AbstractRawLotDetail):
    """Detail for raw purchase transaction lot"""

    purchase_lot_number = models.ForeignKey(
        RawPurchaseLot, on_delete=models.CASCADE, related_name="raw_purchase_lot"
    )


class RawSaleAndReturn(ID, UserAwareModel, NextSerial, DateTimeAwareModel):
    """Raw return or sale"""

    person = models.ForeignKey(Person, on_delete=models.CASCADE, null=True)
    manual_serial = models.PositiveBigIntegerField()
    serial = models.PositiveBigIntegerField()
    transaction_type = models.CharField(
        max_length=10, choices=RawSaleAndReturnTypes.choices
    )

    @classmethod
    def is_serial_unique(cls, **kwargs):
        return not RawSaleAndReturn.objects.filter(**kwargs).exists()


class RawSaleAndReturnWithPurchaseLotRelation(ID):
    """Raw sale/return and lot relation"""

    sale_and_return = models.ForeignKey(RawSaleAndReturn, on_delete=models.CASCADE)
    purchase_lot_number = models.ForeignKey(RawPurchaseLot, on_delete=models.CASCADE)


class RawSaleAndReturnLotDetail(AbstractRawLotDetail):
    """Raw sale/return detail for each lot"""

    sale_and_return_id = models.ForeignKey(
        RawSaleAndReturnWithPurchaseLotRelation, on_delete=models.CASCADE
    )
    nature = models.CharField(
        max_length=1, choices=TransactionChoices.choices, default=TransactionChoices.DEBIT
    )
