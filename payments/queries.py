from .models import Payment, PaymentImage


class PaymentQuery:
    def get_queryset(self):
        return Payment.objects.filter(person__branch=self.request.branch)


class PaymentImageQuery:
    def get_queryset(self):
        return PaymentImage.objects.filter(payment__person__branch=self.request.branch)
