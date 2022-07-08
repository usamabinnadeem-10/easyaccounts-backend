from datetime import date
from functools import reduce

from authentication.models import UserAwareModel
from cheques.choices import ChequeStatusChoices, PersonalChequeStatusChoices
from cheques.models import ExternalChequeHistory, PersonalCheque
from core.constants import MIN_POSITIVE_VAL_SMALL
from core.models import ID, DateTimeAwareModel
from core.utils import get_cheque_account
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _
from essentials.choices import PersonChoices
from essentials.models import AccountType, Person
from expenses.models import ExpenseDetail


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

    @classmethod
    def get_account_payable_receivable(cls, branch, date=None):
        """calculate total payable and receivable"""
        date_filter = {"date__lte": date} if date is not None else {}
        balances = (
            Ledger.objects.values("nature", "person__name")
            .order_by("nature")
            .filter(person__branch=branch, **date_filter)
            .exclude(person__person_type=PersonChoices.EQUITY)
            .exclude(person__person_type=PersonChoices.EXPENSE_ADVANCE)
            .annotate(balance=Sum("amount"))
        )
        data = {}
        for b in balances:
            person = b["person__name"]
            amount = b["balance"]
            nature = b["nature"]
            if not person in data:
                data[person] = amount if nature == "C" else -amount
            else:
                data[person] += amount if nature == "C" else -amount

        payable = 0
        receivable = 0
        for key, value in data.items():
            if value <= 0.0:
                receivable += abs(value)
            else:
                payable += abs(value)

        return {
            "payable": payable,
            "receivable": receivable,
        }

    @classmethod
    def get_total_account_balance(cls, branch, date=None, exclude_cheque=False):
        """calculates total balances in account types"""
        date_filter = {"date__lte": date} if date is not None else {}
        exclude_filter = {}
        if exclude_cheque:
            cheque_account = get_cheque_account(branch).account
            exclude_filter.update({"account_type": cheque_account})
        balances = (
            Ledger.objects.values("nature")
            .order_by("nature")
            .filter(account_type__isnull=False, person__branch=branch, **date_filter)
            .exclude(**exclude_filter)
            .annotate(total=Sum("amount"))
        )
        personal_cheques = (
            PersonalCheque.objects.filter(
                status=PersonalChequeStatusChoices.CLEARED,
                person__branch=branch,
                **date_filter,
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )
        cheques_history = (
            ExternalChequeHistory.objects.filter(
                return_cheque__isnull=True,
                parent_cheque__person__branch=branch,
                **date_filter,
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )
        if exclude_cheque:
            account_balances = (
                AccountType.objects.exclude(id=cheque_account.id).aggregate(
                    total=Sum("opening_balance")
                )["total"]
                or 0
            )
        else:
            account_balances = (
                AccountType.objects.aggregate(total=Sum("opening_balance"))["total"] or 0
            )

        expenses = reduce(
            lambda prev, curr: prev + curr["total"],
            ExpenseDetail.calculate_total_expenses_with_category(branch, None, date),
            0,
        )

        credits = list(filter(lambda x: x["nature"] == "C", balances))
        debits = list(filter(lambda x: x["nature"] == "D", balances))

        return {
            "credit": (credits[0]["total"] if len(credits) else 0)
            + account_balances
            + cheques_history,
            "debit": (debits[0]["total"] if len(debits) else 0)
            + personal_cheques
            + expenses,
        }

    @classmethod
    def get_total_owners_equity(cls, branch, date=None):
        """calculates the total owner equity ledgers"""
        date_filter = {"date__lte": date} if date is not None else {}
        equity = (
            Ledger.objects.values("nature")
            .order_by("nature")
            .filter(
                person__person_type=PersonChoices.EQUITY,
                person__branch=branch,
                **date_filter,
            )
            .annotate(total=Sum("amount"))
        )
        credits = list(filter(lambda x: x["nature"] == "C", equity))
        credits = credits[0]["total"] if len(credits) else 0
        debits = list(filter(lambda x: x["nature"] == "D", equity))
        debits = debits[0]["total"] if len(debits) else 0

        return credits - debits


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

    @classmethod
    def create_ledger_entry(cls, raw_transaction, amount):
        ledger_instance = Ledger.objects.create(
            nature="C",
            person=raw_transaction.person,
            date=raw_transaction.date,
            amount=amount,
        )
        LedgerAndRawTransaction.objects.create(
            ledger_entry=ledger_instance, raw_transaction=raw_transaction
        )
        pass


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


class LedgerAndDetail(ID):
    ledger_entry = models.ForeignKey(
        Ledger, on_delete=models.CASCADE, related_name="ledger_detail"
    )
    detail = models.CharField(max_length=1000)
