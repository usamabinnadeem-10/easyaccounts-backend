from django.db import models
from django.core.validators import MinValueValidator
from django.db.models import Max

from uuid import uuid4
from datetime import date

from essentials.models import AccountType, Person

# Al Baraka Bank (Pakistan) Limited
# Allied Bank Limited
# Askari Bank
# Bank Alfalah Limited
# Bank Al-Habib Limited
# BankIslami Pakistan Limited
# Citi Bank
# Deutsche Bank A.G
# The Bank of Tokyo-Mitsubishi UFJ
# Dubai Islamic Bank Pakistan Limited
# Faysal Bank Limited
# First Women Bank Limited
# Habib Bank Limited
# Standard Chartered Bank (Pakistan) Limited
# Habib Metropolitan Bank Limited
# Industrial and Commercial Bank of China
# Industrial Development Bank of Pakistan
# JS Bank Limited
# MCB Bank Limited
# MCB Islamic Bank Limited
# Meezan Bank Limited
# National Bank of Pakistan


class BankChoices(models.TextChoices):
    MEEZAN = "meezan", "Meezan Bank Limited"
    AL_BARAKA = "al_baraka", "Al Baraka Bank (Pakistan) Limited"
    HABIB_METRO = "habib_metro", "Habib Metropolitan Bank Limited"


class Cheque(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    serial = models.PositiveBigIntegerField()
    cheque_number = models.CharField(max_length=20)
    bank = models.CharField(max_length=20, choices=BankChoices.choices)
    date = models.DateField(default=date.today)
    due_date = models.DateField()
    is_passed = models.BooleanField(default=False)
    amount = models.FloatField(validators=[MinValueValidator(1.0)])

    @classmethod
    def get_next_serial(cls):
        return (Cheque.objects.aggregate(Max("serial"))["serial__max"] or 0) + 1


class ChequeHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    cheque = models.ForeignKey(
        Cheque, on_delete=models.SET_NULL, null=True, related_name="cheque_history"
    )
    account_type = models.ForeignKey(AccountType, on_delete=models.SET_NULL, null=True)
    amount = models.FloatField(validators=[MinValueValidator(1.0)])
    return_cheque = models.ForeignKey(
        Cheque, on_delete=models.SET_NULL, null=True, related_name="return_cheque"
    )
