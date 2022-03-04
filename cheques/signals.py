from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import ExternalChequeHistory


@receiver(post_delete, sender=ExternalChequeHistory)
def delete_external_cheques_upon_history_deletion(sender, instance, **kwargs):
    try:
        if instance.return_cheque:
            instance.return_cheque.delete()
    except:
        pass
