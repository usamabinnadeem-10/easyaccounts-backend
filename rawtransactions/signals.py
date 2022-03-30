from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import RawDebitLot


@receiver(post_delete, sender=RawDebitLot)
def delete_raw_debit(sender, instance, **kwargs):
    try:
        if instance.bill_number:
            instance.bill_number.delete()
    except:
        pass
