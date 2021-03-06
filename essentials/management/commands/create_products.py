from authentication.models import Branch
from django.core.management.base import BaseCommand, CommandError
from essentials.models import Product, ProductCategory


class Command(BaseCommand):
    help = "Creates the white products"

    def add_arguments(self, parser):
        parser.add_argument("product_name", type=str)
        parser.add_argument("color_start", type=int)
        parser.add_argument("color_end", type=int)
        parser.add_argument("branch_name", type=str)
        parser.add_argument("category", type=str)

    def handle(self, *args, **options):
        records = []
        branch_name = options["branch_name"]
        category = options["category"]
        try:
            branch = Branch.objects.get(name=branch_name)
        except Branch.DoesNotExist:
            raise CommandError(f"Branch {branch_name} does not exist")

        try:
            _category = ProductCategory.objects.get(name=category, branch=branch)
        except ProductCategory.DoesNotExist:
            raise CommandError(f"Category {category} does not exist")

        color_start = options["color_start"]
        color_end = options["color_end"]
        product = options["product_name"]
        for color in list(range(color_start, color_end + 1)):
            product_name = f"{product}-{color}"
            records.append(Product(name=product_name, category=_category))

        Product.objects.bulk_create(records)
        self.stdout.write(
            self.style.SUCCESS(
                f"{product} / {category} created with colors {color_start} - {color_end}"
            )
        )
