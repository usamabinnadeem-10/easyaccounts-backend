from django.db import transaction
from django.core.management.base import BaseCommand

from transactions.models import Transaction, TransactionDetail
from transactions.factories import TransactionFactory, TransactionDetailFactory
from essentials.factories import (
    ProductHeadFactory,
    ProductColorFactory,
    ProductFactory,
    WarehouseFactory,
    PersonFactory,
)

NUM_TRANSACTIONS = 10000
NUM_TRANSACTION_DETAILS_PER_TRANSACTION = 10


class Command(BaseCommand):

    help = "Generating Test Data"

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Deleting old data...")
        models = [Transaction, TransactionDetail]
        for m in models:
            m.objects.all().delete()

        self.stdout.write("Creating new data...")

        # making all essentials
        product_color = ProductColorFactory()
        product_head = ProductHeadFactory()
        product = ProductFactory(product_head=product_head, product_color=product_color)
        warehouse = WarehouseFactory()
        person = PersonFactory()

        # adding transactions
        for _ in range(NUM_TRANSACTIONS):
            transaction = TransactionFactory(person=person)
            # adding transaction details to this transaction
            for _ in range(NUM_TRANSACTION_DETAILS_PER_TRANSACTION):
                transaction_detail = TransactionDetailFactory(
                    transaction=transaction, product=product, warehouse=warehouse
                )
