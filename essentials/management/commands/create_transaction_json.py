import json
import os

from django.core.management.base import BaseCommand, CommandError
from transactions.models import Transaction, TransactionDetail


class Command(BaseCommand):
    help = "Creates a transaction"

    def add_arguments(self, parser):
        parser.add_argument("branch_name", type=str)
        parser.add_argument("file", type=str)

    def handle(self, *args, **options):
        file = options["file"]
        path = os.path.dirname(os.path.abspath(__file__)) + f"/data/{file}.json"
        try:
            with open(path, "r") as f:
                data = json.load(f)
                detail = data.pop("transaction_detail")
                transaction = Transaction.objects.create(**data)
                detail_records = []
                for d in detail:
                    detail_records.append(TransactionDetail(transaction=transaction, **d))
                TransactionDetail.objects.bulk_create(detail_records)
        except IOError:
            raise CommandError(f"{file}.json does not exist")
        self.stdout.write(
            self.style.SUCCESS(
                f"Transaction created with serial {transaction.get_computer_serial()}"
            )
        )
