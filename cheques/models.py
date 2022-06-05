from datetime import date

from authentication.models import UserAwareModel
from core.models import ID, DateTimeAwareModel, NextSerial
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Count, Max, Sum
from essentials.choices import LinkedAccountChoices
from essentials.models import AccountType, LinkedAccount, Person
from rest_framework import serializers

from .choices import *


class AbstractCheque(ID, UserAwareModel, DateTimeAwareModel, NextSerial):
    serial = models.PositiveBigIntegerField()
    cheque_number = models.CharField(max_length=20)
    bank = models.CharField(max_length=20, choices=BankChoices.choices)
    due_date = models.DateField()
    amount = models.FloatField(validators=[MinValueValidator(1.0)])
    person = models.ForeignKey(Person, on_delete=models.CASCADE)

    class Meta:
        abstract = True
        unique_together = ("bank", "cheque_number")
        ordering = ["serial", "due_date"]


class ExternalCheque(AbstractCheque):
    status = models.CharField(
        max_length=20,
        choices=ChequeStatusChoices.choices,
        default=ChequeStatusChoices.PENDING,
    )
    is_passed_with_history = models.BooleanField(default=False)

    @classmethod
    def get_amount_recovered(cls, person, branch):
        try:
            cheque_account = LinkedAccount.objects.get(
                name=LinkedAccountChoices.CHEQUE_ACCOUNT, account__branch=branch
            ).account
        except:
            raise serializers.ValidationError("Please create a cheque account first", 400)

        external_recovered = (
            ExternalChequeHistory.objects.filter(
                parent_cheque__person=person, parent_cheque__person__branch=branch
            )
            .exclude(
                account_type=cheque_account,
            )
            .exclude(parent_cheque__status=ChequeStatusChoices.CLEARED)
            .aggregate(sum_history_credits=Sum("amount"))
        )
        recovered = external_recovered.get("sum_history_credits", 0)
        if recovered is not None:
            return recovered
        return 0

    @classmethod
    def get_sum_of_transferred_cheques(cls, person, branch):
        amount = ExternalCheque.objects.filter(
            person__branch=branch, person=person, status=ChequeStatusChoices.TRANSFERRED
        ).aggregate(amount=Sum("amount"))
        amount = amount.get("amount", 0)
        if amount is not None:
            return amount
        return 0

    @classmethod
    def get_number_of_pending_cheques(cls, person, branch):
        pending_count = ExternalCheque.objects.filter(
            person__branch=branch, person=person, status=ChequeStatusChoices.PENDING
        ).aggregate(count=Count("id"))
        pending_count = pending_count.get("count", 0)
        if pending_count is not None:
            return pending_count
        return 0

    @classmethod
    def get_sum_of_cleared_transferred_cheques(cls, person, branch):
        cleared = ExternalCheque.objects.filter(
            person__branch=branch,
            person=person,
            status=ChequeStatusChoices.COMPLETED_TRANSFER,
        ).aggregate(total=Sum("amount"))
        cleared = cleared.get("total", 0)
        if cleared is not None:
            return cleared
        return 0


class PersonalCheque(AbstractCheque):
    account_type = models.ForeignKey(AccountType, on_delete=models.SET_NULL, null=True)
    status = models.CharField(
        max_length=12,
        choices=PersonalChequeStatusChoices.choices,
        default=PersonalChequeStatusChoices.PENDING,
    )

    @classmethod
    def get_pending_cheques(cls, person, branch):
        amount = PersonalCheque.objects.filter(
            person__branch=branch,
            person=person,
            status=PersonalChequeStatusChoices.PENDING,
        ).aggregate(amount=Sum("amount"))
        amount = amount.get("amount", 0)
        if amount is not None:
            return amount
        return 0


class ExternalChequeHistory(ID, UserAwareModel, DateTimeAwareModel):
    parent_cheque = models.ForeignKey(
        ExternalCheque,
        on_delete=models.CASCADE,
        related_name="parent_cheque",
    )
    cheque = models.ForeignKey(
        ExternalCheque,
        on_delete=models.CASCADE,
        null=True,
        related_name="cheque_history",
    )
    account_type = models.ForeignKey(AccountType, on_delete=models.SET_NULL, null=True)
    amount = models.FloatField(validators=[MinValueValidator(1.0)])
    return_cheque = models.ForeignKey(
        ExternalCheque,
        on_delete=models.CASCADE,
        null=True,
        related_name="return_cheque",
    )

    class Meta:
        verbose_name_plural = "External cheque history"

    @classmethod
    def get_remaining_amount(cls, external_cheque, cheque_account, branch):
        """Returns the remaining amount of an external cheque"""
        filter = {}
        # if parent cheque
        if external_cheque.parent_cheque.exists():
            filter.update({"parent_cheque": external_cheque})
        # if child cheque
        else:
            filter.update({"cheque": external_cheque})

        recovered_amount = (
            ExternalChequeHistory.objects.values("parent_cheque__id")
            .filter(parent_cheque__person__branch=branch, **filter)
            .exclude(account_type=cheque_account)
            .annotate(amount=Sum("amount"))
        )
        passed_cheque_amount = (
            ExternalChequeHistory.objects.values("parent_cheque__id")
            .filter(
                parent_cheque__person__branch=branch,
                return_cheque__status__in=[
                    ChequeStatusChoices.CLEARED,
                    ChequeStatusChoices.COMPLETED_HISTORY,
                ],
                **filter
            )
            .annotate(amount=Sum("amount"))
        )
        final_amount = external_cheque.amount
        if len(recovered_amount):
            final_amount -= recovered_amount[0]["amount"]
        if len(passed_cheque_amount):
            final_amount -= passed_cheque_amount[0]["amount"]
        return final_amount if final_amount > 0 else 0

    @classmethod
    def get_amount_received(cls, parent_cheque, branch):
        """Returns the total amount received regardless if hard cash or not"""
        amount = ExternalChequeHistory.objects.filter(
            cheque=parent_cheque, parent_cheque__person__branch=branch
        ).aggregate(total=Sum("amount"))
        amount = amount.get("total", 0)
        amount = amount if amount else 0
        return amount


class ExternalChequeTransfer(ID, UserAwareModel):
    cheque = models.OneToOneField(
        ExternalCheque,
        on_delete=models.CASCADE,
    )
    person = models.ForeignKey(Person, on_delete=models.CASCADE)

    @classmethod
    def sum_of_transferred(cls, person, branch):
        transferred = ExternalChequeTransfer.objects.filter(
            person=person,
            cheque__status=ChequeStatusChoices.TRANSFERRED,
            cheque__person__branch=branch,
        ).aggregate(total=Sum("cheque__amount"))
        transferred = transferred.get("total", 0)
        if transferred is not None:
            return transferred
        return 0
