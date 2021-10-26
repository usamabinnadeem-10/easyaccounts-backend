from django.db import models
import uuid
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator

from essentials.models import AccountType, Person
from transactions.models import Transaction

from datetime import date


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
