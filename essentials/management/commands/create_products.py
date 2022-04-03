from authentication.models import Branch
from django.core.management.base import BaseCommand, CommandError
from essentials.models import Product


class Command(BaseCommand):
    help = "Creates the white products"

    def add_arguments(self, parser):
        parser.add_argument("product_name", type=str)
        parser.add_argument("color_start", type=int)
        parser.add_argument("color_end", type=int)
        parser.add_argument("branch_name", type=str)

    def handle(self, *args, **options):
        records = []
        try:
            branch = Branch.objects.get(name=options["branch_name"])
        except Branch.DoesNotExist:
            raise CommandError(f"Branch {options['branch_name']} does not exist")

        color_start = options["color_start"]
        color_end = options["color_end"]
        product = options["product_name"]
        for color in list(range(color_start, color_end + 1)):
            product_name = f"{product} - {color}"
            records.append(Product(name=product_name, branch_id=branch.id))

        Product.objects.bulk_create(records)
        self.stdout.write(
            self.style.SUCCESS(
                f"{product} created with colors {color_start} - {color_end}"
            )
        )
