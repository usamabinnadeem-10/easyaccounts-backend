import factory
from factory.django import DjangoModelFactory

from .models import Person, Warehouse, AccountType, Product, ProductHead, ProductColor


class PersonFactory(DjangoModelFactory):
    class Meta:
        model = Person

    name = "Lallu Khan"
    person_type = "C"
    business_name = "Lallu Khan and Co."


class WarehouseFactory(DjangoModelFactory):
    class Meta:
        model = Warehouse

    name = "FF-10"
    address = "Gulberg Square"


class AccountTypeFactory(DjangoModelFactory):
    class Meta:
        model = AccountType

    name = "Cash"


class ProductHeadFactory(DjangoModelFactory):
    class Meta:
        model = ProductHead

    head_name = "Al-Khair 44 Yards"


class ProductColorFactory(DjangoModelFactory):
    class Meta:
        model = ProductColor

    color_name = "10"


class ProductFactory(DjangoModelFactory):
    class Meta:
        model = Product

    si_unit = "piece"
    basic_unit = 44
    product_head = factory.SubFactory(ProductHeadFactory)
    product_color = factory.SubFactory(ProductColorFactory)
