from datetime import date
from functools import reduce

from authentication.models import BranchAwareModel
from cheques.choices import ChequeStatusChoices
from cheques.models import ExternalCheque, PersonalCheque
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _
from essentials.models import AccountType, Person
from rawtransactions.models import RawDebit, RawTransaction
from transactions.models import Transaction


class TransactionChoices(models.TextChoices):
    CREDIT = "C", _("Credit")
    DEBIT = "D", _("Debit")


class Ledger(BranchAwareModel):
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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
    raw_transaction = models.ForeignKey(
        RawTransaction, on_delete=models.CASCADE, null=True
    )
    raw_debit = models.ForeignKey(RawDebit, on_delete=models.CASCADE, null=True)

    class Meta:
        ordering = ["date"]

    @classmethod
    def get_external_cheque_balance(cls, person, branch):
        all_external_cheques = (
            Ledger.objects.values("nature")
            .filter(
                branch=branch,
                external_cheque__isnull=False,
                person=person,
                external_cheque__person=person,
            )
            .exclude(external_cheque__status=ChequeStatusChoices.RETURNED)
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
    def get_passed_cheque_amount(cls, person, branch):
        total = Ledger.objects.filter(
            branch=branch,
            external_cheque__isnull=False,
            person=person,
            external_cheque__is_passed_with_history=False,
            external_cheque__person=person,
            external_cheque__status=ChequeStatusChoices.CLEARED,
        ).aggregate(total=Sum("external_cheque__amount"))
        total = total.get("total", 0)
        if total is not None:
            return total
        return 0
