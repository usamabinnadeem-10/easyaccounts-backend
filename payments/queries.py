from .models import Payment, PaymentAndImage, PaymentImage


class PaymentAndImageQuery:
    def get_queryset(self):
        return PaymentAndImage.objects.filter(payment__person__branch=self.request.branch)


class PaymentImageQuery:
    def get_queryset(self):
        return PaymentImage.objects.all()


class PaymentQuery:
    def get_queryset(self):
        return Payment.objects.filter(person__branch=self.request.branch).order_by(
            "serial"
        )
