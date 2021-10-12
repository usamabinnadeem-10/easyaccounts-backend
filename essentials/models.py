from django.db import models
from django.utils.translation import gettext_lazy as _
from uuid import uuid4

class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=50)

class ProductVariant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    product_id = models.ForeignKey(Product, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)


class Warehouse(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=50)
    address = models.CharField(max_length=50)


class AccountChoices(models.TextChoices):
    CREDIT = 'S', _('Supplier')
    DEBIT = 'C', _('Customer')


class Account(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=100)
    account_type = models.CharField(
        max_length=1,
        choices=AccountChoices.choices
        )
    business_name = models.CharField(max_length=100)
