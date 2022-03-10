from .models import ExpenseAccount, ExpenseDetail


class ExpenseAccountQuery:
    def get_queryset(self):
        return ExpenseAccount.objects.filter(branch=self.request.branch)


class ExpenseDetailQuery:
    def get_queryset(self):
        return ExpenseDetail.objects.filter(branch=self.request.branch)
