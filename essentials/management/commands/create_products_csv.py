import csv
import os

from authentication.models import Branch
from django.core.management.base import BaseCommand, CommandError
from essentials.models import Product, ProductCategory


class Command(BaseCommand):
    help = "Creates the default list of products via csv"

    def add_arguments(self, parser):
        parser.add_argument("branch_name", type=str)
        parser.add_argument("file", type=str)

    def handle(self, *args, **options):
        products = []
        branch_name = options["branch_name"]
        file = options["file"]
        path = os.path.dirname(os.path.abspath(__file__)) + f"/data/{file}.csv"
        try:
            branch = Branch.objects.get(name=branch_name)
        except Branch.DoesNotExist:
            raise CommandError(f"Branch {branch_name} does not exist")
        try:
            with open(path) as file:
                reader = csv.reader(file, delimiter=",")
                for row in reader:
                    category, created = ProductCategory.objects.get_or_create(
                        name=row[1], branch_id=branch.id
                    )
                    products.append(
                        Product(
                            name=row[0],
                            category=category,
                        )
                    )
        except IOError:
            raise CommandError(f"{file}.csv does not exist")
        Product.objects.bulk_create(products)
        self.stdout.write(self.style.SUCCESS(f"Products added"))
