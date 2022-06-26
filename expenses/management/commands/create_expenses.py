import csv
import os
from datetime import datetime

from authentication.models import Branch
from django.core.management.base import BaseCommand, CommandError
from essentials.models import AccountType
from expenses.models import ExpenseAccount, ExpenseDetail


class Command(BaseCommand):
    help = "Creates the default list of persons"

    def add_arguments(self, parser):
        parser.add_argument("branch_name", type=str)
        parser.add_argument("file", type=str)
        parser.add_argument("account_type", type=str)
        parser.add_argument("date", type=str)

    def _data_or_null(self, data):
        return data if data else None

    def handle(self, *args, **options):
        branch_name = options["branch_name"]
        account_type_name = options["account_type"]
        file = options["file"]
        opening_date = datetime.strptime(options["date"], "%Y-%m-%d %H:%M:%S")

        path = os.path.dirname(os.path.abspath(__file__)) + f"/data/{file}.csv"

        try:
            branch = Branch.objects.get(name=branch_name)
        except Branch.DoesNotExist:
            raise CommandError(f"Branch {branch_name} does not exist")

        try:
            account_type = AccountType.objects.get(name=account_type_name)
        except AccountType.DoesNotExist:
            raise CommandError(f"Account type {account_type_name} does not exist")

        try:
            opening_amount = 0.0
            with open(path) as file:
                reader = csv.reader(file, delimiter=",")
                for row in reader:

                    expense_account = ExpenseAccount.objects.get_or_create(
                        name=self._data_or_null(row[0]),
                        type=self._data_or_null(row[1]),
                    )
                    amount = self._data_or_null(row[2])
                    expense_detail = ExpenseDetail.objects.create(
                        expense=expense_account,
                        detail="Opening expense",
                        amount=amount,
                        account_type=account_type,
                        serial=ExpenseDetail.get_next_serial(
                            "serial", expense__branch=branch
                        ),
                        date=opening_date,
                    )
                    opening_amount += amount
                account_type.opening_balance = (
                    account_type.opening_balance + opening_amount
                )
                account_type.save()
        except IOError:
            raise CommandError(f"{file}.csv does not exist")

        self.stdout.write(self.style.SUCCESS(f"Expenses created"))
