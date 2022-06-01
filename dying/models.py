from datetime import date

from authentication.models import BranchAwareModel, UserAwareModel
from core.models import ID, DateTimeAwareModel, NextSerial
from django.db import models
from essentials.models import Product, Warehouse
from rawtransactions.models import AbstractRawLotDetail, Formula, RawTransactionLot


class DyingUnit(BranchAwareModel):

    name = models.CharField(max_length=256)

    class Meta:
        unique_together = ("name", "branch")

    def __str__(self):
        return self.name


class DyingIssue(ID, UserAwareModel, DateTimeAwareModel, NextSerial):

    dying_unit = models.ForeignKey(DyingUnit, on_delete=models.CASCADE)
    dying_lot_number = models.PositiveBigIntegerField()

    @classmethod
    def create_auto_issued_lot(cls, branch, dying_unit, lot_number, **kwargs):
        instance = DyingIssue.objects.create(
            dying_unit=DyingUnit.objects.get(id=dying_unit),
            dying_lot_number=DyingIssue.get_next_serial(branch, "dying_lot_number"),
            **kwargs
        )
        DyingIssueLot.objects.create(dying_lot=instance, lot_number=lot_number)


class DyingIssueLot(ID):

    dying_lot = models.ForeignKey(
        DyingIssue, on_delete=models.CASCADE, related_name="dying_issue_lot"
    )
    lot_number = models.ForeignKey(RawTransactionLot, on_delete=models.CASCADE)


class DyingIssueDetail(ID):

    dying_lot_number = models.ForeignKey(
        DyingIssueLot, on_delete=models.CASCADE, related_name="dying_issue_lot_number"
    )
    quantity = models.PositiveIntegerField()
    actual_gazaana = models.FloatField()
    expected_gazaana = models.FloatField()
    formula = models.ForeignKey(Formula, on_delete=models.PROTECT)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)


# class WashingReturn(BranchAwareModel):

#     lot_number = models.ForeignKey(DyingIssue, on_delete=models.CASCADE)
#     date = models.DateField(default=date.today)


# class WashingReturnDetail(AbstractRawLotDetail):

#     product = models.ForeignKey(Product, on_delete=models.CASCADE)
#     quantity = models.FloatField()


# class WashingReturnType
