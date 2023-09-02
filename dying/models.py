from datetime import date

from django.db import models

from authentication.models import BranchAwareModel, UserAwareModel
from core.models import ID, DateTimeAwareModel, NextSerial
from essentials.models import Product, Warehouse
from rawtransactions.models import AbstractRawLotDetail, Formula, RawTransactionLot


class DyingUnit(BranchAwareModel):
    name = models.CharField(max_length=256)

    class Meta:
        unique_together = ("name", "branch")

    def __str__(self):
        return self.name


class DyingIssue(UserAwareModel, DateTimeAwareModel, BranchAwareModel, NextSerial):
    dying_unit = models.ForeignKey(DyingUnit, on_delete=models.CASCADE)
    manual_serial = models.PositiveBigIntegerField()
    serial = models.PositiveBigIntegerField()

    @classmethod
    def create_dying_issue(cls, data, **kwargs):
        user = kwargs.get("user", None)
        branch = kwargs.get("branch", None)
        lots = data.pop("lots")

        dying_issue_instance = DyingIssue.objects.create(
            **data, user=user, serial=DyingIssue.get_next_serial("serial", branch=branch)
        )

        for lot in lots:
            dying_issue_lot_instance = DyingIssueLot.objects.create(
                dying_issue=dying_issue_instance,
                raw_lot_number=lot["raw_lot_number"],
                lot_serial=DyingIssueLot.get_next_serial(
                    "lot_serial", dying_issue__branch=branch
                ),
            )
            current_details = []
            for detail in lot["detail"]:
                current_details.append(
                    DyingIssueDetail(dying_issue_lot=dying_issue_lot_instance, **detail)
                )
            DyingIssueDetail.objects.bulk_create(current_details)

    @classmethod
    def create_auto_issued_lot(cls, lots):
        pass


class DyingIssueLot(ID, NextSerial):
    dying_issue = models.ForeignKey(DyingIssue, on_delete=models.CASCADE)
    raw_lot_number = models.PositiveBigIntegerField()
    lot_serial = models.PositiveBigIntegerField()


class DyingIssueDetail(ID):
    dying_issue_lot = models.ForeignKey(DyingIssueLot, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    actual_gazaana = models.FloatField()
    expected_gazaana = models.FloatField()
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, null=True)
