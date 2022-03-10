from .models import Ledger


class LedgerQuery:
    def get_queryset(self):
        return Ledger.objects.filter(branch=self.request.branch)
