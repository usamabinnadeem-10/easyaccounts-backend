from authentication.models import BranchAwareModel, UserAwareModel
from core.models import ID, DateTimeAwareModel, NextSerial
from django.db import models
from essentials.models import AccountType


class ExpenseAccount(BranchAwareModel):
    name = models.CharField(max_length=100)


class ExpenseDetail(ID, UserAwareModel, DateTimeAwareModel, NextSerial):
    expense = models.ForeignKey(ExpenseAccount, on_delete=models.CASCADE)
    detail = models.TextField(max_length=1000)
    amount = models.FloatField()
    account_type = models.ForeignKey(AccountType, on_delete=models.SET_NULL, null=True)
    serial = models.PositiveBigIntegerField()

    class Meta:
        ordering = ["date"]
