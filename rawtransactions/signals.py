from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import RawSaleAndReturnWithPurchaseLotRelation


@receiver(post_delete, sender=RawSaleAndReturnWithPurchaseLotRelation)
def delete_raw_debit(sender, instance, **kwargs):
    try:
        if instance.sale_and_return:
            instance.sale_and_return.delete()
    except:
        pass
