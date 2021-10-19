from django.db import models
from uuid import uuid4

from essentials.models import AccountType


class ExpenseAccount(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    name = models.CharField(max_length=100)


class ExpenseDetail(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    date = models.DateField(auto_now_add=True)
    expense = models.ForeignKey(ExpenseAccount, on_delete=models.CASCADE)
    detail = models.TextField(max_length=1000)
    amount = models.FloatField()
    account_type = models.ForeignKey(AccountType, on_delete=models.SET_NULL, null=True)
