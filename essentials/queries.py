from .models import Person, Warehouse, Area, AccountType, Product, Stock, LinkedAccount


class PersonQuery:
    def get_queryset(self):
        return Person.objects.filter(branch=self.request.branch)


class WarehouseQuery:
    def get_queryset(self):
        return Warehouse.objects.filter(branch=self.request.branch)


class AreaQuery:
    def get_queryset(self):
        return Area.objects.filter(branch=self.request.branch)


class AccountTypeQuery:
    def get_queryset(self):
        return AccountType.objects.filter(branch=self.request.branch)


class ProductQuery:
    def get_queryset(self):
        return Product.objects.filter(branch=self.request.branch)


class StockQuery:
    def get_queryset(self):
        return Stock.objects.filter(branch=self.request.branch)


class LinkedAccountQuery:
    def get_queryset(self):
        return LinkedAccount.objects.filter(branch=self.request.branch)
