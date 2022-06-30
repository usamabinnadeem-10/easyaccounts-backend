from .models import Ledger, LedgerAndDetail


class LedgerQuery:
    def get_queryset(self):
        return Ledger.objects.filter(person__branch=self.request.branch).prefetch_related(
            "ledger_transaction",
            "ledger_external_cheque",
            "ledger_personal_cheque",
            "ledger_raw_transaction",
            "ledger_raw_debit",
        )


class LedgerAndDetailQuery:
    def get_queryset(self):
        return LedgerAndDetail.objects.filter(
            ledger_entry__person__branch=self.request.branch
        )
