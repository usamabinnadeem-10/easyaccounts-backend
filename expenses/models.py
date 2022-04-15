from datetime import date
from uuid import uuid4

from authentication.models import BranchAwareModel, UserAwareModel
from django.db import models
from essentials.models import AccountType


class ExpenseAccount(BranchAwareModel, UserAwareModel):
    name = models.CharField(max_length=100)


class ExpenseDetail(BranchAwareModel):
    date = models.DateField(default=date.today)
    expense = models.ForeignKey(ExpenseAccount, on_delete=models.CASCADE)
    detail = models.TextField(max_length=1000)
    amount = models.FloatField()
    account_type = models.ForeignKey(AccountType, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ["date"]
