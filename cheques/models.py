from django.db import models
from django.db.models import Sum, Max, Count
from django.core.validators import MinValueValidator

from rest_framework import serializers

from uuid import uuid4
from datetime import date

from essentials.models import AccountType, Person, LinkedAccount
from .choices import *
from .constants import CHEQUE_ACCOUNT


class AbstractCheque(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    serial = models.PositiveBigIntegerField()
    cheque_number = models.CharField(max_length=20)
    bank = models.CharField(max_length=20, choices=BankChoices.choices)
    date = models.DateField(default=date.today)
    due_date = models.DateField()
    amount = models.FloatField(validators=[MinValueValidator(1.0)])
    person = models.ForeignKey(Person, on_delete=models.CASCADE)

    class Meta:
        abstract = True
        unique_together = ("bank", "cheque_number")
        ordering = ["serial", "due_date"]

    @classmethod
    def get_next_serial(cls):
        return (cls.objects.aggregate(Max("serial"))["serial__max"] or 0) + 1


class ExternalCheque(AbstractCheque):
    status = models.CharField(
        max_length=20,
        choices=ChequeStatusChoices.choices,
        default=ChequeStatusChoices.PENDING,
    )
    is_passed_with_history = models.BooleanField(default=False)

    @classmethod
    def get_amount_recovered(cls, person):
        try:
            cheque_account = LinkedAccount.objects.get(name=CHEQUE_ACCOUNT).account
        except:
            raise serializers.ValidationError(
                "Please create a cheque account first", 400
            )

        external_recovered = (
            ExternalChequeHistory.objects.filter(parent_cheque__person=person)
            .exclude(account_type=cheque_account)
            .aggregate(sum_history_credits=Sum("amount"))
        )
        recovered = external_recovered.get("sum_history_credits", 0)
        if recovered is not None:
            return recovered
        return 0

    @classmethod
    def get_sum_of_transferred_cheques(cls, person):
        amount = ExternalCheque.objects.filter(
            person=person, status=ChequeStatusChoices.TRANSFERRED
        ).aggregate(amount=Sum("amount"))
        amount = amount.get("amount", 0)
        if amount is not None:
            return amount
        return 0

    @classmethod
    def get_number_of_pending_cheques(cls, person):
        pending_count = ExternalCheque.objects.filter(
            status=ChequeStatusChoices.PENDING
        ).aggregate(count=Count("id"))
        pending_count = pending_count.get("count", 0)
        if pending_count is not None:
            return pending_count
        return 0


class PersonalCheque(AbstractCheque):
    account_type = models.ForeignKey(AccountType, on_delete=models.SET_NULL, null=True)
    status = models.CharField(
        max_length=12,
        choices=PersonalChequeStatusChoices.choices,
        default=PersonalChequeStatusChoices.PENDING,
    )

    @classmethod
    def get_pending_cheques(cls, person):
        amount = PersonalCheque.objects.filter(
            person=person, status=PersonalChequeStatusChoices.PENDING
        ).aggregate(amount=Sum("amount"))
        amount = amount.get("amount", 0)
        if amount is not None:
            return amount
        return 0


class ExternalChequeHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
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
    date = models.DateField(default=date.today)

    @classmethod
    def get_remaining_amount(cls, parent_cheque, cheque_account):
        recovered_amount = (
            ExternalChequeHistory.objects.values("parent_cheque__id")
            .filter(parent_cheque=parent_cheque)
            .exclude(account_type=cheque_account)
            .annotate(amount=Sum("amount"))
        )
        if len(recovered_amount):
            return parent_cheque.amount - recovered_amount[0]["amount"]
        return parent_cheque.amount

    @classmethod
    def get_amount_received(cls, parent_cheque):
        amount = ExternalChequeHistory.objects.filter(
            parent_cheque=parent_cheque
        ).aggregate(total=Sum("amount"))
        amount = amount.get("total", 0)
        amount = amount if amount else 0
        return amount


class ExternalChequeTransfer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    cheque = models.OneToOneField(
        ExternalCheque,
        on_delete=models.CASCADE,
    )
    person = models.ForeignKey(Person, on_delete=models.CASCADE)

    @classmethod
    def sum_of_transferred(cls, person):
        transferred = ExternalChequeTransfer.objects.filter(person=person).aggregate(
            total=Sum("cheque__amount")
        )
        transferred = transferred.get("total", 0)
        if transferred is not None:
            return transferred
        return 0
