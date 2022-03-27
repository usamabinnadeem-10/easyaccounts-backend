from .models import RawProduct, RawTransaction, Formula


class RawProductQuery:
    def get_queryset(self):
        return RawProduct.objects.filter(branch=self.request.branch)


class RawTransactionQuery:
    def get_queryset(self):
        return RawTransaction.objects.filter(branch=self.request.branch)


class FormulaQuery:
    def get_queryset(self):
        return Formula.objects.filter(branch=self.request.branch)
