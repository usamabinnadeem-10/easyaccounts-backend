from authentication.choices import RoleChoices

from .models import Payment, PaymentAndImage, PaymentImage


class PaymentAndImageQuery:
    def get_queryset(self):
        return PaymentAndImage.objects.filter(payment__person__branch=self.request.branch)


class PaymentImageQuery:
    def get_queryset(self):
        return PaymentImage.objects.all()


class PaymentQuery:
    def get_queryset(self):
        filter = {}
        if self.request.role not in [
            RoleChoices.ADMIN,
            RoleChoices.ADMIN_VIEWER,
            RoleChoices.HEAD_ACCOUNTANT,
            RoleChoices.ACCOUNTANT,
        ]:
            filter.update({"person__person_type": "C"})
        return Payment.objects.filter(
            person__branch=self.request.branch, **filter
        ).order_by("serial")
