from .models import Payment


class PaymentQuery:
    def get_queryset(self):
        return Payment.objects.filter(person__branch=self.request.branch)
