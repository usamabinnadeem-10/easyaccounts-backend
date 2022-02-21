from django.db import models
from django.core.validators import MinValueValidator
from django.db.models import Max

from uuid import uuid4
from datetime import date

from essentials.models import AccountType, Person
from .choices import *


class AbstractCheque(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    serial = models.PositiveBigIntegerField()
    cheque_number = models.CharField(max_length=20)
    bank = models.CharField(max_length=20, choices=BankChoices.choices)
    date = models.DateField(default=date.today)
    due_date = models.DateField()
    is_passed = models.BooleanField(default=False)
    is_returned = models.BooleanField(default=False)
    amount = models.FloatField(validators=[MinValueValidator(1.0)])

    class Meta:
        abstract = True
        unique_together = ("bank", "cheque_number")

    @classmethod
    def get_next_serial(cls):
        return (cls.objects.aggregate(Max("serial"))["serial__max"] or 0) + 1


class ExternalCheque(AbstractCheque):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=12,
        choices=ChequeStatusChoices.choices,
        default=ChequeStatusChoices.PENDING,
    )


class PersonalCheque(AbstractCheque):
    issued_to = models.ForeignKey(Person, on_delete=models.CASCADE)
    account_type = models.ForeignKey(AccountType, on_delete=models.SET_NULL, null=True)


class ExternalChequeHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    parent_cheque = models.ForeignKey(
        ExternalCheque,
        on_delete=models.CASCADE,
        related_name="parent_cheque",
    )
    cheque = models.ForeignKey(
        ExternalCheque,
        on_delete=models.SET_NULL,
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


class ExternalChequeTransfer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    cheque = models.OneToOneField(
        ExternalCheque,
        on_delete=models.CASCADE,
    )
    person = models.ForeignKey(Person, on_delete=models.CASCADE)


# TODOs:
## set a status on cheque (parent) which would indicate where the cheque is rn in its lifecycle
