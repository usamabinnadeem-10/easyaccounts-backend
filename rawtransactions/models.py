from authentication.models import BranchAwareModel, UserAwareModel
from core.constants import MIN_POSITIVE_VAL_SMALL
from core.models import ID, DateTimeAwareModel, NextSerial
from django.core.validators import MinValueValidator
from django.db import models
from dying.models import DyingIssue
from essentials.models import Person, Warehouse
from ledgers.models import Ledger, LedgerAndRawPurchase, LedgerAndRawSaleAndReturn
from rest_framework import serializers, status
from transactions.choices import TransactionChoices

from .choices import RawProductTypes, RawSaleAndReturnTypes
from .utils import calculate_amount


class Formula(BranchAwareModel):
    """Raw product formulas"""

    numerator = models.FloatField()
    denominator = models.FloatField()

    def __str__(self):
        return f"{self.numerator}/{self.denominator}"


class AbstractRawLotDetail(ID):

    quantity = models.FloatField(validators=[MinValueValidator(MIN_POSITIVE_VAL_SMALL)])
    actual_gazaana = models.FloatField(
        validators=[MinValueValidator(MIN_POSITIVE_VAL_SMALL)]
    )
    expected_gazaana = models.FloatField(
        validators=[MinValueValidator(MIN_POSITIVE_VAL_SMALL)]
    )
    rate = models.FloatField(validators=[MinValueValidator(MIN_POSITIVE_VAL_SMALL)])
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

    @classmethod
    def make_transaction(cls, data, branch, user, isEdit=False, editInstance=None):
        lots = data.pop("lots")
        transaction = RawPurchase.objects.create(
            **data,
            serial=RawPurchase.get_next_serial("serial", person__branch=branch),
            user=user,
        )
        amount = 0
        for lot in lots:
            current_lot = RawPurchaseLot.objects.create(
                raw_purchase=transaction,
                issued=lot["issued"],
                raw_product=lot["raw_product"],
                lot_number=RawPurchaseLot.get_next_serial(
                    "lot_number", raw_purchase__person__branch=branch
                ),
            )
            if current_lot.issued:
                try:
                    DyingIssue.create_auto_issued_lot(
                        branch=branch,
                        dying_unit=lot["dying_unit"],
                        lot_number=current_lot,
                        date=transaction.date,
                    )
                except:
                    raise serializers.ValidationError(
                        "Please enter dying unit for issued lot"
                    )

            current_lot_detail = map(
                lambda l: {
                    **l,
                    "warehouse": None if current_lot.issued else l["warehouse"],
                },
                lot["lot_detail"],
            )

            for detail in current_lot_detail:
                current_detail = RawPurchaseLotDetail.objects.create(
                    **detail, purchase_lot_number=current_lot
                )
                amount += (
                    current_detail.quantity
                    * current_detail.rate
                    * current_detail.actual_gazaana
                    * (
                        current_detail.formula.numerator
                        / current_detail.formula.denominator
                    )
                )

        LedgerAndRawPurchase.create_ledger_entry(transaction, amount)

        return {
            "id": transaction.id,
            "person": transaction.person,
            "manual_serial": transaction.manual_serial,
            "date": transaction.date,
            "lots": lots,
        }


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

    @classmethod
    def make_transaction(cls, data, user, branch, isEdit=False, editInstance=None):

        sale_and_return_instance = RawSaleAndReturn.objects.create(
            **data,
            user=user,
            serial=RawSaleAndReturn.get_next_serial(
                "serial",
                transaction_type=data["transaction_type"],
                person__branch=branch,
            ),
        )
        ledger_amount = 0
        for lot in data:
            ledger_amount += calculate_amount(lot["detail"])
            raw_debit_lot_relation = (
                RawSaleAndReturnWithPurchaseLotRelation.objects.create(
                    purchase_lot_number=lot["purchase_lot_number"],
                    sale_and_return=sale_and_return_instance,
                )
            )
            current_return_details = []
            for detail in lot["detail"]:
                current_return_details.append(
                    RawSaleAndReturnLotDetail(
                        sale_and_return_id=raw_debit_lot_relation,
                        **detail,
                    )
                )

            RawSaleAndReturnLotDetail.objects.bulk_create(current_return_details)

        LedgerAndRawSaleAndReturn.create_ledger_entry(
            sale_and_return_instance, ledger_amount
        )


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


class RawStockTransfer(ID, DateTimeAwareModel, NextSerial):

    from_warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    serial = models.PositiveBigIntegerField()
    manual_serial = models.PositiveBigIntegerField()


class RawStockTransferAndLotRelation(ID):

    raw_transfer = models.ForeignKey(RawStockTransfer, on_delete=models.CASCADE)
    purchase_lot_number = models.ForeignKey(RawPurchaseLot, on_delete=models.CASCADE)


class RawStockTransferLotDetail(ID):

    raw_stock_transfer_id = models.ForeignKey(
        RawStockTransferAndLotRelation, on_delete=models.CASCADE
    )
    quantity = models.FloatField(validators=[MinValueValidator(MIN_POSITIVE_VAL_SMALL)])
    actual_gazaana = models.FloatField(
        validators=[MinValueValidator(MIN_POSITIVE_VAL_SMALL)]
    )
    expected_gazaana = models.FloatField(
        validators=[MinValueValidator(MIN_POSITIVE_VAL_SMALL)]
    )
    formula = models.ForeignKey(Formula, on_delete=models.PROTECT)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, null=True)
