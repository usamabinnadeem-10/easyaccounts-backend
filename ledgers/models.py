from datetime import date
from functools import reduce

from authentication.models import BranchAwareModel, UserAwareModel
from cheques.choices import ChequeStatusChoices
from cheques.models import ExternalCheque, PersonalCheque
from core.constants import MIN_POSITIVE_VAL_SMALL
from core.models import DateTimeAwareModel
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _
from essentials.models import AccountType, Person
from rawtransactions.models import RawDebit, RawTransaction


class TransactionChoices(models.TextChoices):
    CREDIT = "C", _("Credit")
    DEBIT = "D", _("Debit")


class Ledger(BranchAwareModel, UserAwareModel, DateTimeAwareModel):
    detail = models.TextField(max_length=1000, null=True, blank=True)
    amount = models.FloatField(validators=[MinValueValidator(MIN_POSITIVE_VAL_SMALL)])
    nature = models.CharField(max_length=1, choices=TransactionChoices.choices)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    account_type = models.ForeignKey(AccountType, on_delete=models.SET_NULL, null=True)
    transaction = models.ForeignKey(
        "transactions.Transaction", on_delete=models.CASCADE, null=True
    )
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
                person__branch=branch,
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
            person__branch=branch,
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

    @classmethod
    def create_ledger_string(cls, detail):
        """creates ledger string for the transaction details"""
        string = ""
        for d in list(detail):
            string += (
                f"{float(d['quantity'])} thaan "
                f"{d['product'].name} ({d['yards_per_piece']} Yards) "
                f"@ PKR {str(d['rate'])} per yard\n"
            )
        return string

    @classmethod
    def create_ledger_entry_for_transasction(cls, t_data):
        """creates ledger entries for transaction"""
        transaction = t_data["transaction"]
        t_detail = t_data["detail"]
        amount = reduce(
            lambda prev, curr: prev
            + (curr["yards_per_piece"] * curr["quantity"] * curr["rate"]),
            list(t_detail),
            0,
        )
        amount -= transaction.discount
        ledger_string = Ledger.create_ledger_string(t_detail)
        ledger_data = [
            Ledger(
                **{
                    "detail": ledger_string,
                    "amount": amount,
                    "transaction": transaction,
                    "user": transaction.user,
                    "nature": transaction.nature,
                    "person": transaction.person,
                    "date": transaction.date,
                    "branch": transaction.branch,
                }
            )
        ]
        if t_data["paid"]:
            ledger_data.append(
                Ledger(
                    **{
                        "detail": f"Paid on {transaction.account_type.name}",
                        "amount": transaction.paid_amount,
                        "transaction": transaction,
                        "nature": "C",
                        "account_type": transaction.account_type,
                        "person": transaction.person,
                        "date": transaction.date,
                        "branch": transaction.branch,
                    }
                )
            )
        Ledger.objects.bulk_create(ledger_data)
