from django.db import models
from django.utils.translation import gettext_lazy as _
from uuid import uuid4


class ProductVariant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=50)

    def __str__(self) -> str:
        return self.name


class QuantityChoices(models.TextChoices):
    CREDIT = 'yards', _('Yards')
    DEBIT = 'piece', _('Pieces')

class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=50)
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True)
    unit = models.CharField(
        max_length=5,
        choices=QuantityChoices.choices
    )


    def __str__(self) -> str:
        return self.name + ': ' + self.variant


class Warehouse(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=50)
    address = models.CharField(max_length=50, null=True)

    def __str__(self) -> str:
        return self.name

class PersonChoices(models.TextChoices):
    CREDIT = 'S', _('Supplier')
    DEBIT = 'C', _('Customer')


"""Supplier or Customer Account"""
class Person(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=100)
    person_type = models.CharField(
        max_length=1,
        choices=PersonChoices.choices
        )
    business_name = models.CharField(max_length=100, null=True)

    def __str__(self) -> str:
        return self.name + ': ' + self.person_type


"""Account types like cash account or cheque account"""
class AccountType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=100)

    def __str__(self) -> str:
        return self.name