from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from uuid import uuid4

from essentials.models import Warehouse, Product, Person


class ID(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)


class TransactionChoices(models.TextChoices):
    CREDIT = "C", _("Credit")
    DEBIT = "D", _("Debit")


class Transaction(ID):
    date = models.DateField(auto_now_add=True)
    nature = models.CharField(max_length=1, choices=TransactionChoices.choices)
    discount = models.FloatField(validators=[MinValueValidator(0.0)])
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    draft = models.BooleanField(default=False)


class TransactionDetail(ID):
    transaction_id = models.ForeignKey(
        Transaction, on_delete=models.CASCADE, related_name="transaction_detail"
    )
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    rate = models.FloatField(validators=[MinValueValidator(0.0)])
    quantity = models.FloatField(validators=[MinValueValidator(1.0)])
