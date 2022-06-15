from datetime import date
from functools import reduce

from authentication.models import UserAwareModel
from cheques.choices import ChequeStatusChoices
from core.constants import MIN_POSITIVE_VAL_SMALL
from core.models import ID, DateTimeAwareModel
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _
from essentials.models import AccountType, Person


class TransactionChoices(models.TextChoices):
    CREDIT = "C", _("Credit")
    DEBIT = "D", _("Debit")


class Ledger(ID, UserAwareModel, DateTimeAwareModel):
    amount = models.FloatField(validators=[MinValueValidator(MIN_POSITIVE_VAL_SMALL)])
    nature = models.CharField(max_length=1, choices=TransactionChoices.choices)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    account_type = models.ForeignKey(AccountType, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ["date"]

    @classmethod
    def get_external_cheque_balance(cls, person, branch):
        all_external_cheques = (
            Ledger.objects.values("nature")
            .filter(
                person__branch=branch,
                ledger_external_cheque__isnull=False,
                person=person,
                ledger_external_cheque__person=person,
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
        ledger_instance = Ledger.objects.create(
            **{
                "amount": amount,
                "user": transaction.user,
                "nature": transaction.nature,
                "person": transaction.person,
                "date": transaction.date,
            }
        )
        LedgerAndTransaction.objects.create(
            ledger_entry=ledger_instance, transaction=transaction
        )


class LedgerAndTransaction(ID):
    """Ledger and Transaction link"""

    ledger_entry = models.ForeignKey(
        Ledger, on_delete=models.CASCADE, related_name="ledger_transaction"
    )
    transaction = models.ForeignKey(
        "transactions.Transaction",
        on_delete=models.CASCADE,
    )


class LedgerAndExternalCheque(ID):
    """Ledger and External Cheque link"""

    ledger_entry = models.ForeignKey(
        Ledger, on_delete=models.CASCADE, related_name="ledger_external_cheque"
    )
    external_cheque = models.ForeignKey(
        "cheques.ExternalCheque",
        on_delete=models.CASCADE,
    )

    @classmethod
    def get_external_cheque_balance(cls, person, branch):
        all_external_cheques = (
            LedgerAndExternalCheque.objects.values("ledger_entry__nature")
            .filter(
                ledger_entry__person__branch=branch,
                external_cheque__isnull=False,
                ledger_entry__person=person,
                external_cheque__person=person,
            )
            .exclude(external_cheque__status=ChequeStatusChoices.RETURNED)
            .annotate(amount=Sum("external_cheque__amount"))
        )

        balance_of_external_cheques = reduce(
            lambda prev, curr: prev
            + (
                curr["amount"] if curr["ledger_entry__nature"] == "C" else -curr["amount"]
            ),
            all_external_cheques,
            0,
        )

        return balance_of_external_cheques

    @classmethod
    def get_passed_cheque_amount(cls, person, branch):
        total = LedgerAndExternalCheque.objects.filter(
            ledger_entry__person__branch=branch,
            external_cheque__isnull=False,
            ledger_entry__person=person,
            external_cheque__is_passed_with_history=False,
            external_cheque__person=person,
            external_cheque__status=ChequeStatusChoices.CLEARED,
        ).aggregate(total=Sum("external_cheque__amount"))
        total = total.get("total", 0)
        if total is not None:
            return total
        return 0


class LedgerAndPersonalCheque(ID):
    """Ledger and Personal Cheque link"""

    ledger_entry = models.ForeignKey(
        Ledger, on_delete=models.CASCADE, related_name="ledger_personal_cheque"
    )
    personal_cheque = models.ForeignKey(
        "cheques.PersonalCheque",
        on_delete=models.CASCADE,
    )


class LedgerAndRawTransaction(ID):
    ledger_entry = models.ForeignKey(
        Ledger, on_delete=models.CASCADE, related_name="ledger_raw_transaction"
    )
    raw_transaction = models.ForeignKey(
        "rawtransactions.RawTransaction",
        on_delete=models.CASCADE,
    )


class LedgerAndRawDebit(ID):
    ledger_entry = models.ForeignKey(
        Ledger, on_delete=models.CASCADE, related_name="ledger_raw_debit"
    )
    raw_debit = models.ForeignKey("rawtransactions.RawDebit", on_delete=models.CASCADE)


class LedgerAndPayment(ID):
    ledger_entry = models.ForeignKey(
        Ledger, on_delete=models.CASCADE, related_name="ledger_payment"
    )
    payment = models.ForeignKey(
        "payments.Payment", on_delete=models.CASCADE, related_name="payment_ledger"
    )

    @classmethod
    def create_ledger_entry(cls, payment):
        ledger_instance = Ledger.objects.create(
            amount=payment.amount,
            nature=payment.nature,
            person=payment.person,
            account_type=payment.account_type,
            date=payment.date,
        )
        LedgerAndPayment.objects.create(ledger_entry=ledger_instance, payment=payment)


# class LedgerAndTransactionAndPayment(ID):
#     ledger_entry = models.ForeignKey(
#         Ledger,
#         on_delete=models.SET_NULL,
#         related_name="ledger_transaction_payment",
#         null=True,
#     )
#     payment = models.ForeignKey(
#         "payments.Payment",
#         on_delete=models.CASCADE,
#         related_name="payment_ledger_transaction",
#     )
#     transaction = models.ForeignKey(
#         "transactions.Transaction",
#         on_delete=models.SET_NULL,
#         null=True,
#         related_name="transaction_ledger_payment",
#     )

#     @classmethod
#     def create_ledger_entry(cls, payment, transaction):
#         ledger_instance = Ledger.objects.create(
#             amount=payment.amount,
#             nature=payment.nature,
#             person=payment.person,
#             account_type=payment.account_type,
#             date=payment.date,
#         )
#         LedgerAndTransactionAndPayment.objects.create(
#             ledger_entry=ledger_instance, payment=payment, transaction=transaction
#         )
