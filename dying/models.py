from django.db import models

from authentication.models import BranchAwareModel
from rawtransactions.models import RawTransactionLot, Formula

from datetime import date


class DyingUnit(BranchAwareModel):

    name = models.CharField(max_length=256)


class DyingIssue(BranchAwareModel):

    dying_unit = models.ForeignKey(DyingUnit, on_delete=models.CASCADE)
    lot_number = models.ForeignKey(RawTransactionLot, on_delete=models.CASCADE)
    dying_lot_number = models.PositiveBigIntegerField()
    date = models.DateField(default=date.today)


class DyingIssueDetail(BranchAwareModel):

    dying_lot_number = models.ForeignKey(DyingIssue, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    actual_gazaana = models.FloatField()
    expected_gazaana = models.FloatField()
    formula = models.ForeignKey(Formula, on_delete=models.PROTECT)
