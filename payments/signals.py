from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import PaymentAndImage


@receiver(post_delete, sender=PaymentAndImage)
def delete_images_if_payment_is_deleted(sender, instance, **kwargs):
    print(instance)
    try:
        if instance.image:
            instance.image.delete()
    except:
        pass
