import csv
import os
from datetime import datetime

from authentication.models import Branch
from django.core.management.base import BaseCommand, CommandError
from essentials.models import Area, Person
from ledgers.models import Ledger, LedgerAndDetail


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
        ledgers = []
        ledgers_and_details = []
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
            with open(path, mode="r", encoding="utf-8-sig") as file:
                reader = csv.reader(file, delimiter=",")
                for row in reader:
                    data = {
                        "name": self._data_or_null(row[0]),
                        "person_type": self._data_or_null(row[4]),
                        "address": self._data_or_null(row[1]),
                        "phone_number": self._clean_phone_number(row[3]),
                        "branch": branch,
                    }
                    AREA = self._data_or_null(row[5])
                    if AREA is not None:
                        AREA, created = Area.objects.get_or_create(
                            name=row[5], branch_id=branch.id
                        )
                        data.update({"area": AREA})
                    person = Person(**data)
                    persons.append(person)
                    balance = self._data_or_null(row[2])
                    if balance and abs(float(balance)) > 0.0:
                        ledger = Ledger(
                            amount=abs(balance),
                            person=person,
                            nature="C" if balance > 0.0 else "D",
                            date=opening_date,
                        )
                        ledgers.append(ledger)
                        ledgers_and_details.append(
                            LedgerAndDetail(ledger_entry=ledger, detail="Opening Balance")
                        )
        except IOError:
            raise CommandError(f"{file}.csv does not exist")
        Person.objects.bulk_create(persons)
        Ledger.objects.bulk_create(ledgers)
        LedgerAndDetail.objects.bulk_create(ledgers_and_details)
        self.stdout.write(self.style.SUCCESS(f"Persons created"))
