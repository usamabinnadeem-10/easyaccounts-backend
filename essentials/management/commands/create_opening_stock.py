import csv
import os

from authentication.models import Branch
from django.core.management.base import BaseCommand, CommandError
from essentials.models import Product, Stock, Warehouse


class Command(BaseCommand):
    help = "Creates opening stock"

    def add_arguments(self, parser):
        parser.add_argument("file", type=str)
        parser.add_argument(
            "--delete",
            action="store_true",
            dest="delete",
            default=False,
            help="Delete all the previous opening stock",
        )
        parser.add_argument(
            "-b",
            "--branch",
            type=str,
            help="Branch name for deleting the opening stock for",
        )

    def handle(self, *args, **options):
        file = options["file"]
        delete = options["delete"]
        branch = options["branch"]
        path = os.path.dirname(os.path.abspath(__file__)) + f"/data/{file}.csv"

        try:
            with open(path, mode="r", encoding="utf-8-sig") as file:
                reader = csv.reader(file, delimiter=",")
                product = None
                warehouse = None
                if delete:
                    try:
                        branch = Branch.objects.get(name=branch)
                        Stock.objects.filter(warehouse__branch=branch).delete()
                    except Branch.DoesNotExist:
                        raise CommandError(f"Branch {branch} does not exist")

                for row in reader:
                    CURR_PROD = row[0]
                    CURR_WAREHOUSE = row[1]
                    if product is None:
                        product = Product.objects.get(name=CURR_PROD)
                    else:
                        if product.name != CURR_PROD:
                            product = Product.objects.get(name=CURR_PROD)

                    if warehouse is None:
                        warehouse = Warehouse.objects.get(name=CURR_WAREHOUSE)
                    else:
                        if warehouse.name != CURR_WAREHOUSE:
                            warehouse = Warehouse.objects.get(name=CURR_WAREHOUSE)

                    stock, created = Stock.objects.get_or_create(
                        product=product, warehouse=warehouse, yards_per_piece=row[2]
                    )
                    stock.opening_stock = row[3]
                    stock.opening_stock_rate = row[4]
                    stock.save()
        except IOError:
            raise CommandError(f"{file}.csv does not exist")
        self.stdout.write(self.style.SUCCESS(f"Stock created"))
