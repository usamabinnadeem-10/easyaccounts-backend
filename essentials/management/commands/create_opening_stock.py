import csv
import os

from django.core.management.base import BaseCommand, CommandError
from essentials.models import Product, Stock, Warehouse

RATES = {"AK": 88, "KS": 80}


class Command(BaseCommand):
    help = "Creates opening stock"

    def add_arguments(self, parser):
        parser.add_argument("file", type=str)

    def handle(self, *args, **options):
        file = options["file"]
        path = os.path.dirname(os.path.abspath(__file__)) + f"/data/{file}.csv"

        try:
            with open(path) as file:
                reader = csv.reader(file, delimiter=",")
                product = None
                warehouse = None
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

                    rate = RATES[product.category.name]
                    stock, created = Stock.objects.get_or_create(
                        product=product, warehouse=warehouse, yards_per_piece=row[2]
                    )
                    stock.opening_stock = row[3]
                    stock.opening_stock_rate = rate
                    stock.save()
        except IOError:
            raise CommandError(f"{file}.csv does not exist")
        self.stdout.write(self.style.SUCCESS(f"Stock created"))
