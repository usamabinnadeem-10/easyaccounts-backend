from django.db import models

from essentials.models import AccountType, ID

from datetime import date


class ExpenseAccount(ID):
    name = models.CharField(max_length=100)


class ExpenseDetail(ID):
    date = models.DateField(default=date.today)
    expense = models.ForeignKey(ExpenseAccount, on_delete=models.CASCADE)
    detail = models.TextField(max_length=1000)
    amount = models.FloatField()
    account_type = models.ForeignKey(AccountType, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ["date"]
