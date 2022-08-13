from .models import Formula, RawProduct, RawPurchase, RawPurchaseLot, RawSaleAndReturn


class RawProductQuery:
    def get_queryset(self):
        return RawProduct.objects.filter(person__branch=self.request.branch)


class RawPurchaseQuery:
    def get_queryset(self):
        return RawPurchase.objects.filter(person__branch=self.request.branch)


class FormulaQuery:
    def get_queryset(self):
        return Formula.objects.filter(branch=self.request.branch)


class RawPurchaseLotQuery:
    def get_queryset(self):
        return RawPurchaseLot.objects.filter(
            raw_purchase__person__branch=self.request.branch
        ).order_by("-lot_number")


class RawSaleAndReturnQuery:
    def get_queryset(self):
        return RawSaleAndReturn.objects.filter(person__branch=self.request.branch)
