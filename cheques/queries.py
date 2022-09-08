from .models import (
    ExternalCheque,
    ExternalChequeHistory,
    ExternalChequeTransfer,
    PersonalCheque,
)


class ExternalChequeQuery:
    def get_queryset(self):
        return ExternalCheque.objects.filter(person__branch=self.request.branch).order_by(
            "due_date"
        )


class ExternalChequeHistoryQuery:
    def get_queryset(self):
        return ExternalChequeHistory.objects.filter(
            parent_cheque__person__branch=self.request.branch
        )


class ExternalChequeTransferQuery:
    def get_queryset(self):
        return ExternalChequeTransfer.objects.filter(
            cheque__person__branch=self.request.branch
        )


class PersonalChequeQuery:
    def get_queryset(self):
        return PersonalCheque.objects.filter(person__branch=self.request.branch).order_by(
            "due_date"
        )
