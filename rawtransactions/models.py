from functools import reduce

from django.core.validators import MinValueValidator
from django.db import models

from authentication.models import Branch, BranchAwareModel, UserAwareModel
from core.constants import MIN_POSITIVE_VAL_SMALL
from core.models import ID, DateTimeAwareModel, NextSerial
from essentials.models import Person, Warehouse
from transactions.choices import TransactionChoices

from .choices import RawDebitTypes, RawProductTypes

"""Helper Classes"""


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
    rate_gazaana = models.FloatField(validators=[MinValueValidator(1.0)])
    rate = models.FloatField(validators=[MinValueValidator(1.0)])
    formula = models.ForeignKey(Formula, on_delete=models.PROTECT, null=True)
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


"""Raw Transaction Classes"""


class RawTransaction(ID, UserAwareModel, NextSerial, DateTimeAwareModel):
    """Raw transaction"""

    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True)
    person = models.ForeignKey(Person, on_delete=models.CASCADE, null=True)
    manual_serial = models.PositiveBigIntegerField()
    serial = models.PositiveBigIntegerField()

    def __str__(self):
        return f"{self.serial} - {self.person}"

    @classmethod
    def get_raw_transaction_total(cls, transaction_data):
        lots = transaction_data["lots"]
        amount = reduce(
            lambda prev, curr: prev
            + reduce(
                lambda prev2, curr2: prev2
                + curr2["quantity"] * curr2["rate"] * curr2["rate_gazaana"],
                curr["lot_detail"],
                0,
            ),
            lots,
            0,
        )
        return amount

    @classmethod
    def make_raw_transaction(cls, transaction_data, branch, user):
        lots = transaction_data.pop("lots")
        transaction = RawTransaction.objects.create(
            **transaction_data,
            serial=RawTransaction.get_next_serial("serial", person__branch=branch),
            user=user,
            branch=branch,
        )

        lots_objs = []
        lot_details_objs = []
        for lot in lots:
            current_lot = RawTransactionLot(
                raw_transaction=transaction,
                issued=lot["issued"],
                raw_product=lot["raw_product"],
                lot_number=RawTransactionLot.get_next_serial(
                    "lot_number", raw_transaction__person__branch=branch
                ),
            )
            lots_objs.append(current_lot)
            # if current lot is issued to dying then create dying issue
            # if current_lot.issued:
            #     try:
            #         DyingIssue.create_auto_issued_lot(
            #             branch=branch,
            #             dying_unit=lot["dying_unit"],
            #             lot_number=current_lot,
            #             date=transaction.date,
            #         )
            #     except:
            #         raise serializers.ValidationError(
            #             "Please enter dying unit for issued lot"
            #         )
            current_lot_detail = map(
                lambda l: {
                    **l,
                    "warehouse": None if current_lot.issued else l["warehouse"],
                },
                lot["lot_detail"],
            )

            for detail in current_lot_detail:
                current_detail = RawLotDetail(**detail, lot_number=current_lot)
                lot_details_objs.append(current_detail)

        lots_objs = RawTransactionLot.objects.bulk_create(lots_objs)
        lot_details_objs = RawLotDetail.objects.bulk_create(lot_details_objs)

        return transaction


class RawTransactionLot(ID, NextSerial):
    """Lot for raw transaction"""

    raw_transaction = models.ForeignKey(RawTransaction, on_delete=models.CASCADE)
    raw_product = models.ForeignKey(RawProduct, on_delete=models.PROTECT)
    lot_number = models.PositiveBigIntegerField()
    issued = models.BooleanField(default=False)
    detail = models.CharField(max_length=256, null=True, blank=True)
    warehouse_number = models.PositiveBigIntegerField(null=True)
    dying_number = models.PositiveBigIntegerField(null=True)

    def __str__(self):
        return f"{self.raw_transaction} - {self.lot_number}"


class RawLotDetail(AbstractRawLotDetail):
    """Detail for raw transaction lot"""

    lot_number = models.ForeignKey(
        RawTransactionLot, on_delete=models.CASCADE, related_name="raw_lot_detail"
    )


"""Raw Debit Classes"""


class RawDebit(ID, UserAwareModel, NextSerial, DateTimeAwareModel):
    """Raw return or sale"""

    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True)
    person = models.ForeignKey(Person, on_delete=models.CASCADE, null=True)
    manual_serial = models.PositiveBigIntegerField()
    serial = models.PositiveBigIntegerField()
    debit_type = models.CharField(max_length=10, choices=RawDebitTypes.choices)

    @classmethod
    def is_serial_unique(cls, **kwargs):
        return not RawDebit.objects.filter(**kwargs).exists()

    @classmethod
    def make_raw_debit_transaction(cls, transaction_data, branch, user):
        data = transaction_data.pop("data")
        debit_instance = RawDebit.objects.create(
            **transaction_data,
            user=user,
            branch=branch,
            serial=RawDebit.get_next_serial(
                "serial",
                debit_type=transaction_data["debit_type"],
                branch=branch,
            ),
        )
        debit_lots = []
        debit_lot_details = []
        for lot in data:
            raw_debit_lot_instance = RawDebitLot(
                lot_number=lot["lot_number"],
                bill_number=debit_instance,
            )
            debit_lots.append(raw_debit_lot_instance)

            for detail in lot["detail"]:
                debit_lot_details.append(
                    RawDebitLotDetail(
                        return_lot=raw_debit_lot_instance,
                        **detail,
                    )
                )

        RawDebitLot.objects.bulk_create(debit_lots)
        RawDebitLotDetail.objects.bulk_create(debit_lot_details)

        return debit_instance


class RawDebitLot(ID):
    """Raw debit and lot relation"""

    bill_number = models.ForeignKey(RawDebit, on_delete=models.CASCADE)
    lot_number = models.ForeignKey(RawTransactionLot, on_delete=models.CASCADE)
    detail = models.CharField(max_length=256, null=True, blank=True)


class RawDebitLotDetail(AbstractRawLotDetail):
    """Raw debit detail for each lot"""

    return_lot = models.ForeignKey(RawDebitLot, on_delete=models.CASCADE)


"""Raw Transfer Classes"""


class RawTransfer(ID, UserAwareModel, NextSerial, DateTimeAwareModel):
    """Raw return or sale"""

    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True)
    person = models.ForeignKey(Person, on_delete=models.CASCADE, null=True)
    serial = models.PositiveBigIntegerField()
    manual_serial = models.PositiveBigIntegerField()

    @classmethod
    def is_serial_unique(cls, **kwargs):
        return not RawDebit.objects.filter(**kwargs).exists()

    @classmethod
    def make_raw_transfer_transaction(cls, transaction_data, branch, user):
        data = transaction_data.pop("data")
        debit_instance = RawDebit.objects.create(
            **transaction_data,
            user=user,
            branch=branch,
            serial=RawDebit.get_next_serial(
                "serial",
                debit_type=transaction_data["debit_type"],
                branch=branch,
            ),
        )
        debit_lots = []
        debit_lot_details = []
        for lot in data:
            raw_debit_lot_instance = RawDebitLot(
                lot_number=lot["lot_number"],
                bill_number=debit_instance,
            )
            debit_lots.append(raw_debit_lot_instance)

            for detail in lot["detail"]:
                debit_lot_details.append(
                    RawDebitLotDetail(
                        return_lot=raw_debit_lot_instance,
                        **detail,
                    )
                )

        RawDebitLot.objects.bulk_create(debit_lots)
        RawDebitLotDetail.objects.bulk_create(debit_lot_details)

        return debit_instance


class RawTransferLot(ID):
    """Raw transfer and lot relation"""

    raw_transfer = models.ForeignKey(RawTransfer, on_delete=models.CASCADE)
    lot_number = models.ForeignKey(RawTransactionLot, on_delete=models.CASCADE)


class RawTransferLotDetail(AbstractRawLotDetail):
    """Raw transfer detail for each lot"""

    raw_transfer_lot = models.ForeignKey(RawTransferLot, on_delete=models.CASCADE)
