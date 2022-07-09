from authentication.models import BranchAwareModel, UserAwareModel
from core.models import ID, DateTimeAwareModel, NextSerial
from django.db import models
from django.db.models import Sum
from essentials.models import AccountType

from .choices import ExpenseTypes


class ExpenseAccount(BranchAwareModel):
    name = models.CharField(max_length=100)
    type = models.CharField(
        max_length=14, choices=ExpenseTypes.choices, default=ExpenseTypes.OTHER
    )


class ExpenseDetail(ID, UserAwareModel, DateTimeAwareModel, NextSerial):
    expense = models.ForeignKey(ExpenseAccount, on_delete=models.CASCADE)
    detail = models.TextField(max_length=1000)
    amount = models.FloatField()
    account_type = models.ForeignKey(AccountType, on_delete=models.SET_NULL, null=True)
    serial = models.PositiveBigIntegerField()

    class Meta:
        ordering = ["date"]

    @classmethod
    def calculate_total_expenses_with_category(
        cls, branch, start_date=None, end_date=None
    ):
        """an array of expenses grouped by category for branch with date filter"""
        date_filter = {}
        if start_date:
            date_filter.update({"date__gte": start_date})
        if end_date:
            date_filter.update({"date__lte": end_date})
        return (
            ExpenseDetail.objects.values("expense__type")
            .order_by("serial")
            .filter(expense__branch=branch, **date_filter)
            .annotate(total=Sum("amount"))
        )

    @classmethod
    def calculate_total_expenses(cls, branch, start_date=None, end_date=None):
        """total expenses for a branch with dates"""
        date_filter = {}
        if start_date:
            date_filter.update({"date__gte": start_date})
        if end_date:
            date_filter.update({"date__lte": end_date})

        return (
            ExpenseDetail.objects.filter(expense__branch=branch, **date_filter).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )
