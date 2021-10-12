from django.db import models
import uuid
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator

from essentials.models import AccountType, Person
from transactions.models import Transaction

class TransactionChoices(models.TextChoices):
    CREDIT = 'C', _('Credit')
    DEBIT = 'D', _('Debit')

# Create your models here.
class Ledger(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    date = models.DateTimeField(auto_now_add=True)
    detail = models.TextField(max_length=1000, null=True, blank=True)
    amount = models.FloatField(validators=[MinValueValidator(0.0)])
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE , null=True, blank=True)
    account_type = models.ForeignKey(AccountType, on_delete=models.SET_NULL, null=True)
    nature = models.CharField(
        max_length=1,
        choices=TransactionChoices.choices
        )
