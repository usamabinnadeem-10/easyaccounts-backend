from functools import reduce

from django.core.validators import MinValueValidator
from django.db import models

from authentication.models import Branch, BranchAwareModel, UserAwareModel
from core.constants import MIN_POSITIVE_VAL_SMALL
from core.models import ID, DateTimeAwareModel, NextSerial
from essentials.models import Person, Warehouse
from transactions.choices import TransactionChoices

from .choices import RawDebitTypes, RawProductTypes


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


class RawTransaction(ID, UserAwareModel, NextSerial, DateTimeAwareModel):
    """Raw transaction"""

    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True)
    person = models.ForeignKey(Person, on_delete=models.CASCADE, null=True)
    # manual_invoice_serial = models.PositiveBigIntegerField()
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
        # return {
        #     "data": {
        #         **(transaction.__dict__),
        #         "lots": list(
        #             map(
        #                 lambda lot: {
        #                     **(lot.__dict__),
        #                     "lot_detail": list(
        #                         map(
        #                             lambda x: {**x.__dict__},
        #                             filter(
        #                                 lambda detail: detail.lot_number.id == lot.id,
        #                                 lot_details_objs,
        #                             ),
        #                         )
        #                     ),
        #                 },
        #                 lots_objs,
        #             )
        #         ),
        #     },
        #     "transaction": transaction,
        # }


class RawTransactionLot(ID, NextSerial):
    """Lot for raw transaction"""

    raw_transaction = models.ForeignKey(RawTransaction, on_delete=models.CASCADE)
    raw_product = models.ForeignKey(RawProduct, on_delete=models.PROTECT)
    lot_number = models.PositiveBigIntegerField()
    issued = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.raw_transaction} - {self.lot_number}"


class RawLotDetail(AbstractRawLotDetail):
    """Detail for raw transaction lot"""

    lot_number = models.ForeignKey(
        RawTransactionLot, on_delete=models.CASCADE, related_name="raw_lot_detail"
    )


class RawDebit(ID, UserAwareModel, NextSerial, DateTimeAwareModel):
    """Raw return or sale"""

    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True)
    person = models.ForeignKey(Person, on_delete=models.CASCADE, null=True)
    # manual_invoice_serial = models.PositiveBigIntegerField()
    serial = models.PositiveBigIntegerField()
    debit_type = models.CharField(max_length=10, choices=RawDebitTypes.choices)

    @classmethod
    def is_serial_unique(cls, **kwargs):
        return not RawDebit.objects.filter(**kwargs).exists()


class RawDebitLot(ID):
    """Raw debit and lot relation"""

    bill_number = models.ForeignKey(RawDebit, on_delete=models.CASCADE)
    lot_number = models.ForeignKey(RawTransactionLot, on_delete=models.CASCADE)


class RawDebitLotDetail(AbstractRawLotDetail):
    """Raw debit detail for each lot"""

    return_lot = models.ForeignKey(RawDebitLot, on_delete=models.CASCADE)
    nature = models.CharField(
        max_length=1, choices=TransactionChoices.choices, default=TransactionChoices.DEBIT
    )
