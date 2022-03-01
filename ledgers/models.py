from django.db import models
from django.db.models import Sum

import uuid
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator

from cheques.models import ExternalCheque, PersonalCheque
from essentials.models import AccountType, Person
from transactions.models import Transaction

from datetime import date
from functools import reduce


class TransactionChoices(models.TextChoices):
    CREDIT = "C", _("Credit")
    DEBIT = "D", _("Debit")


class Ledger(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField(default=date.today)
    detail = models.TextField(max_length=1000, null=True, blank=True)
    amount = models.FloatField(validators=[MinValueValidator(0.0)])
    nature = models.CharField(max_length=1, choices=TransactionChoices.choices)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    account_type = models.ForeignKey(AccountType, on_delete=models.SET_NULL, null=True)
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, null=True)
    draft = models.BooleanField(default=False)
    external_cheque = models.ForeignKey(
        ExternalCheque, on_delete=models.CASCADE, null=True
    )
    personal_cheque = models.ForeignKey(
        PersonalCheque, on_delete=models.CASCADE, null=True
    )

    class Meta:
        ordering = ["date"]

    @classmethod
    def get_external_cheque_balance(cls, person):
        all_external_cheques = (
            Ledger.objects.values("nature")
            .filter(
                external_cheque__isnull=False,
                person=person,
                external_cheque__person=person,
            )
            .annotate(amount=Sum("amount"))
        )
        balance_of_external_cheques = reduce(
            lambda prev, curr: prev
            + (curr["amount"] if curr["nature"] == "C" else -curr["amount"]),
            all_external_cheques,
            0,
        )
        return balance_of_external_cheques

    @classmethod
    def get_passed_cheque_amount(cls, person):
        total = Ledger.objects.filter(
            external_cheque__isnull=False,
            person=person,
            external_cheque__is_passed_with_history=False,
        ).aggregate(total=Sum("external_cheque__amount"))
        total = total.get("total", 0)
        if total is not None:
            return total
        return 0
