from .models import Formula, RawDebit, RawProduct, RawTransaction, RawTransactionLot


class RawProductQuery:
    def get_queryset(self):
        return RawProduct.objects.filter(person__branch=self.request.branch)


class RawTransactionQuery:
    def get_queryset(self):
        return RawTransaction.objects.filter(person__branch=self.request.branch)


class FormulaQuery:
    def get_queryset(self):
        return Formula.objects.filter(branch=self.request.branch)


class RawTransactionLotQuery:
    def get_queryset(self):
        return RawTransactionLot.objects.filter(
            raw_transaction__person__branch=self.request.branch
        ).order_by("-lot_number")


class RawDebitQuery:
    def get_queryset(self):
        return RawDebit.objects.filter(person__branch=self.request.branch)
