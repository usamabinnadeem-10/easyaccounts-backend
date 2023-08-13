from .models import (
    AccountType,
    Area,
    LinkedAccount,
    Person,
    Product,
    ProductCategory,
    Stock,
    Warehouse,
)


class PersonQuery:
    def get_queryset(self):
        return Person.objects.filter(
            branch=self.request.branch,
        )


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
        return Product.objects.filter(category__branch=self.request.branch)


class StockQuery:
    def get_queryset(self):
        return Stock.objects.filter(product__branch=self.request.branch)


class LinkedAccountQuery:
    def get_queryset(self):
        return LinkedAccount.objects.filter(account__branch=self.request.branch)


class ProductCategoryQuery:
    def get_queryset(self):
        return ProductCategory.objects.filter(branch=self.request.branch)
