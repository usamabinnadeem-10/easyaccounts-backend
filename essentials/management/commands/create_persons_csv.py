import csv
import os
from datetime import datetime

from authentication.models import Branch
from django.core.management.base import BaseCommand, CommandError
from essentials.models import Area, Person
from ledgers.models import LedgerAndPayment
from payments.models import Payment


class Command(BaseCommand):
    help = "Creates the default list of persons"

    def add_arguments(self, parser):
        parser.add_argument("branch_name", type=str)
        parser.add_argument("file", type=str)
        parser.add_argument("opening_balance_date", type=str)

    def _data_or_null(self, data):
        return data if data else None

    def _clean_phone_number(self, phone):
        phone = self._data_or_null(phone)
        if phone is not None:
            phone = "".join(phone.split("-"))
            return f"+92{phone[1:]}"
        return None

    def handle(self, *args, **options):
        persons = []
        branch_name = options["branch_name"]
        file = options["file"]
        opening_date = datetime.strptime(
            options["opening_balance_date"], "%Y-%m-%d %H:%M:%S"
        )
        path = os.path.dirname(os.path.abspath(__file__)) + f"/data/{file}.csv"
        try:
            branch = Branch.objects.get(name=branch_name)
        except Branch.DoesNotExist:
            raise CommandError(f"Branch {branch_name} does not exist")
        try:
            with open(path) as file:
                reader = csv.reader(file, delimiter=",")
                for row in reader:
                    data = {
                        "name": self._data_or_null(row[0]),
                        "person_type": self._data_or_null(row[4]),
                        "address": self._data_or_null(row[1]),
                        "phone_number": self._clean_phone_number(row[3]),
                        "opening_balance": self._data_or_null(row[2]) or 0.0,
                    }
                    AREA = self._data_or_null(row[5])
                    if AREA is not None:
                        AREA, created = Area.objects.get_or_create(
                            name=row[5], branch_id=branch.id
                        )
                        data.update({"area": AREA})
                    person = Person(**data)
                    persons.append(person)
                    balance = data["opening_balance"]

                    if abs(balance) > 0.0:
                        payment = Payment.objects.create(
                            date=opening_date,
                            detail="Opening Balance",
                            amount=abs(balance),
                            nature="C" if balance > 0.0 else "D",
                            person=person,
                        )
                        LedgerAndPayment.create_ledger_entry(payment)
        except IOError:
            raise CommandError(f"{file}.csv does not exist")
        Person.objects.bulk_create(persons)
        self.stdout.write(self.style.SUCCESS(f"Persons added"))
