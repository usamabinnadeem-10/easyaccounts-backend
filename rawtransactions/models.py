from functools import reduce
from uuid import uuid4

from django.core.validators import MinValueValidator
from django.db import models
from django.shortcuts import get_object_or_404

from authentication.models import ID, Branch, BranchAwareModel, UserAwareModel
from core.constants import MIN_POSITIVE_VAL_SMALL
from core.models import ID, DateTimeAwareModel, NextSerial
from essentials.models import Person, Warehouse

from .choices import RawDebitTypes, RawProductGlueTypes, RawProductTypes

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
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, default=None)

    def __str__(self):
        return f"{self.name}"


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
    def make_raw_transaction(cls, transaction_data, branch, user, **kwargs):
        old_instance = kwargs.get("old_instance")
        old_serial = old_instance.serial if old_instance else None

        # delete old instance in the beginning
        if old_instance:
            old_instance.delete()

        lots = transaction_data.pop("lots")
        transaction = RawTransaction.objects.create(
            **transaction_data,
            serial=old_serial
            if old_serial
            else RawTransaction.get_next_serial("serial", person__branch=branch),
            user=user,
            branch=branch,
        )

        lot_details_objs = []
        dying_lots = []
        for lot in lots:
            old_lot_number = lot.get("lot_number") if old_instance else None
            current_lot = RawTransactionLot.objects.create(
                raw_transaction=transaction,
                issued=lot["issued"],
                raw_product=lot["raw_product"],
                product_glue=lot["product_glue"],
                product_type=lot["product_type"],
                lot_number=old_lot_number
                or RawTransactionLot.get_next_serial(
                    "lot_number", raw_transaction__person__branch=branch
                ),
                warehouse_number=lot["warehouse_number"],
                dying_number=lot["dying_number"],
                detail=lot["detail"],
            )
            # if current lot is issued to dying then create dying issue
            if current_lot.issued and not old_instance:
                dying_lots.append(
                    {
                        "raw_lot_number": current_lot.lot_number,
                    }
                )
                # try:
                #     DyingIssue.create_auto_issued_lot(
                #         branch=branch,
                #         dying_unit=lot["dying_unit"],
                #         lot_number=current_lot,
                #         date=transaction.date,
                #     )
                # except:
                #     raise serializers.ValidationError(
                #         "Please enter dying unit for issued lot"
                #     )
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

        lot_details_objs = RawLotDetail.objects.bulk_create(lot_details_objs)

        return transaction


class RawTransactionLot(ID, NextSerial):
    """Lot for raw transaction"""

    raw_transaction = models.ForeignKey(
        RawTransaction, on_delete=models.CASCADE, related_name="lots"
    )
    raw_product = models.ForeignKey(RawProduct, on_delete=models.PROTECT)
    product_glue = models.CharField(max_length=15, choices=RawProductGlueTypes.choices)
    product_type = models.CharField(max_length=15, choices=RawProductTypes.choices)
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
        RawTransactionLot, on_delete=models.CASCADE, related_name="lot_detail"
    )


"""Raw Debit Classes"""


class RawDebit(ID, UserAwareModel, NextSerial, DateTimeAwareModel):
    """Raw return or sale"""

    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True)
    person = models.ForeignKey(Person, on_delete=models.CASCADE, null=True)
    manual_serial = models.PositiveBigIntegerField()
    serial = models.PositiveBigIntegerField()
    debit_type = models.CharField(max_length=15, choices=RawDebitTypes.choices)

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
            raw_transaction_lot = get_object_or_404(
                RawTransactionLot, lot_number=lot["lot_number"]
            )
            raw_debit_lot_instance = RawDebitLot(
                lot_number=lot["lot_number"],
                bill_number=debit_instance,
                raw_product=raw_transaction_lot.raw_product,
                product_glue=raw_transaction_lot.product_glue,
                product_type=raw_transaction_lot.product_type,
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

    bill_number = models.ForeignKey(
        RawDebit, on_delete=models.CASCADE, related_name="lots"
    )
    lot_number = models.PositiveBigIntegerField(default=1)
    raw_product = models.ForeignKey(RawProduct, on_delete=models.PROTECT, null=True)
    product_glue = models.CharField(max_length=15, choices=RawProductGlueTypes.choices)
    product_type = models.CharField(max_length=15, choices=RawProductTypes.choices)
    detail = models.CharField(max_length=256, null=True, blank=True)


class RawDebitLotDetail(AbstractRawLotDetail):
    """Raw debit detail for each lot"""

    return_lot = models.ForeignKey(
        RawDebitLot, on_delete=models.CASCADE, related_name="lot_detail"
    )


"""Raw Transfer Classes"""


class RawTransfer(ID, UserAwareModel, NextSerial, DateTimeAwareModel):
    """Raw return or sale"""

    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True)
    serial = models.PositiveBigIntegerField()
    manual_serial = models.PositiveBigIntegerField()

    @classmethod
    def is_serial_unique(cls, **kwargs):
        return not RawTransfer.objects.filter(**kwargs).exists()

    @classmethod
    def make_raw_transfer_transaction(cls, transfer_data, branch, user):
        lots = transfer_data.pop("data")
        transfer_instance = RawTransfer.objects.create(
            **transfer_data,
            user=user,
            branch=branch,
            serial=RawTransfer.get_next_serial(
                "serial",
                branch=branch,
            ),
        )

        transfer_lots = []
        transfer_lot_details = []
        for lot in lots:
            raw_transaction_lot = get_object_or_404(
                RawTransactionLot, lot_number=lot["lot_number"]
            )
            raw_transfer_lot_obj = RawTransferLot(
                lot_number=lot["lot_number"],
                raw_transfer=transfer_instance,
                raw_product=raw_transaction_lot.raw_product,
                product_glue=raw_transaction_lot.product_glue,
                product_type=raw_transaction_lot.product_type,
            )
            transfer_lots.append(raw_transfer_lot_obj)
            for detail in lot["detail"]:
                obj = {
                    **detail,
                    "raw_transfer_lot": raw_transfer_lot_obj,
                }
                transfer_lot_details.append(RawTransferLotDetail(**obj))

        RawTransferLot.objects.bulk_create(transfer_lots)
        RawTransferLotDetail.objects.bulk_create(transfer_lot_details)

        return transfer_instance


class RawTransferLot(ID):
    """Raw transfer and lot relation"""

    raw_transfer = models.ForeignKey(
        RawTransfer, on_delete=models.CASCADE, related_name="lots"
    )
    lot_number = models.PositiveBigIntegerField(default=1)
    raw_product = models.ForeignKey(RawProduct, on_delete=models.PROTECT, null=True)
    product_glue = models.CharField(max_length=15, choices=RawProductGlueTypes.choices)
    product_type = models.CharField(max_length=15, choices=RawProductTypes.choices)


class RawTransferLotDetail(models.Model):
    """Raw transfer detail for each lot"""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    transferring_warehouse = models.ForeignKey(
        Warehouse, on_delete=models.PROTECT, related_name="transferring_warehouse"
    )
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(MIN_POSITIVE_VAL_SMALL)]
    )
    actual_gazaana = models.FloatField(validators=[MinValueValidator(1.0)])
    expected_gazaana = models.FloatField(validators=[MinValueValidator(1.0)])
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, null=True)
    raw_transfer_lot = models.ForeignKey(
        RawTransferLot, on_delete=models.CASCADE, related_name="lot_detail"
    )
