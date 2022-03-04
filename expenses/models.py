from django.db import models

from essentials.models import AccountType

from datetime import date
from uuid import uuid4


class ExpenseAccount(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=100)


class ExpenseDetail(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    date = models.DateField(default=date.today)
    expense = models.ForeignKey(ExpenseAccount, on_delete=models.CASCADE)
    detail = models.TextField(max_length=1000)
    amount = models.FloatField()
    account_type = models.ForeignKey(AccountType, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ["date"]
