from .models import Ledger


class LedgerQuery:
    def get_queryset(self):
        return Ledger.objects.filter(person__branch=self.request.branch)
