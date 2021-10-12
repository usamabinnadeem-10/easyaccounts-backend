from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from uuid import uuid4

from essentials.models import Warehouse, Product


class ID(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)


class TransactionChoices(models.TextChoices):
    CREDIT = 'C', _('Credit')
    DEBIT = 'D', _('Debit')

class Transaction(ID):
    time = models.DateTimeField('Time', auto_now_add=True)
    type = models.CharField(
        max_length=1,
        choices=TransactionChoices.choices
        )
    discount = models.FloatField(validators=[MinValueValidator(0.0)])
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True)
    
class TransactionDetail(ID):
    trade_id = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    rate = models.FloatField(validators=[MinValueValidator(0.0)])
    quantity = models.IntegerField(validators=[MinValueValidator(1)])

