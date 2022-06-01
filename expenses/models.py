from authentication.models import BranchAwareModel, UserAwareModel
from core.models import ID, DateTimeAwareModel
from django.db import models
from essentials.models import AccountType


class ExpenseAccount(BranchAwareModel):
    name = models.CharField(max_length=100)


class ExpenseDetail(ID, UserAwareModel, DateTimeAwareModel):
    expense = models.ForeignKey(ExpenseAccount, on_delete=models.CASCADE)
    detail = models.TextField(max_length=1000)
    amount = models.FloatField()
    account_type = models.ForeignKey(AccountType, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ["date"]
