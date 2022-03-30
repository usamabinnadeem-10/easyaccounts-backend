from datetime import date

from authentication.models import BranchAwareModel
from django.db import models
from essentials.models import Warehouse
from rawtransactions.models import Formula, NextSerial, RawTransactionLot


class DyingUnit(BranchAwareModel):

    name = models.CharField(max_length=256)

    class Meta:
        unique_together = ("name", "branch")

    def __str__(self):
        return self.name


class DyingIssue(BranchAwareModel, NextSerial):

    dying_unit = models.ForeignKey(DyingUnit, on_delete=models.CASCADE)
    dying_lot_number = models.PositiveBigIntegerField()
    date = models.DateField(default=date.today)

    @classmethod
    def create_auto_issued_lot(cls, branch, dying_unit, lot_number, **kwargs):
        instance = DyingIssue.objects.create(
            branch=branch,
            dying_unit=DyingUnit.objects.get(id=dying_unit),
            dying_lot_number=DyingIssue.get_next_serial(branch, "dying_lot_number"),
            **kwargs
        )
        DyingIssueLot.objects.create(
            dying_lot=instance, lot_number=lot_number, branch=branch
        )


class DyingIssueLot(BranchAwareModel):

    dying_lot = models.ForeignKey(
        DyingIssue, on_delete=models.CASCADE, related_name="dying_issue_lot"
    )
    lot_number = models.ForeignKey(RawTransactionLot, on_delete=models.CASCADE)


class DyingIssueDetail(BranchAwareModel):

    dying_lot_number = models.ForeignKey(
        DyingIssueLot, on_delete=models.CASCADE, related_name="dying_issue_lot_number"
    )
    quantity = models.PositiveIntegerField()
    actual_gazaana = models.FloatField()
    expected_gazaana = models.FloatField()
    formula = models.ForeignKey(Formula, on_delete=models.PROTECT)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
