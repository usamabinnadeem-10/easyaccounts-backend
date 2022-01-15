import factory
from factory import faker
from factory.django import DjangoModelFactory

from essentials.factories import (
    PersonFactory,
    WarehouseFactory,
    AccountTypeFactory,
    ProductFactory,
)
from .models import Transaction, TransactionDetail


class TransactionFactory(DjangoModelFactory):
    class Meta:
        model = Transaction

    nature = "D"
    person = factory.SubFactory(PersonFactory)
    type = "credit"
    serial = factory.Sequence(lambda n: n)


class TransactionDetailFactory(DjangoModelFactory):
    class Meta:
        model = TransactionDetail

    transaction = factory.SubFactory(TransactionFactory)
    product = factory.SubFactory(ProductFactory)
    warehouse = factory.SubFactory(WarehouseFactory)
    rate = 90
    quantity = 15
    amount = 59400
