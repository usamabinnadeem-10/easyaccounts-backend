from .models import (
    ExternalCheque,
    ExternalChequeHistory,
    ExternalChequeTransfer,
    PersonalCheque,
)


class ExternalChequeQuery:
    def get_queryset(self):
        return ExternalCheque.objects.filter(branch=self.request.branch)


class ExternalChequeHistoryQuery:
    def get_queryset(self):
        return ExternalChequeHistory.objects.filter(branch=self.request.branch)


class ExternalChequeTransferQuery:
    def get_queryset(self):
        return ExternalChequeTransfer.objects.filter(branch=self.request.branch)


class PersonalChequeQuery:
    def get_queryset(self):
        return PersonalCheque.objects.filter(branch=self.request.branch)
