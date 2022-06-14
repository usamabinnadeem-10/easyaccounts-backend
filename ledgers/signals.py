from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import (
    LedgerAndExternalCheque,
    LedgerAndPayment,
    LedgerAndPersonalCheque,
    LedgerAndRawDebit,
    LedgerAndRawTransaction,
    LedgerAndTransaction,
)


@receiver(post_delete, sender=LedgerAndTransaction)
def delete_ledger_entry_for_transaction(sender, instance, **kwargs):
    try:
        if instance.ledger_entry:
            instance.ledger_entry.delete()
    except:
        pass


@receiver(post_delete, sender=LedgerAndExternalCheque)
def delete_ledger_entry_for_external_cheque(sender, instance, **kwargs):
    try:
        if instance.ledger_entry:
            instance.ledger_entry.delete()
    except:
        pass


@receiver(post_delete, sender=LedgerAndPersonalCheque)
def delete_ledger_entry_for_personal_cheque(sender, instance, **kwargs):
    try:
        if instance.ledger_entry:
            instance.ledger_entry.delete()
    except:
        pass


@receiver(post_delete, sender=LedgerAndRawTransaction)
def delete_ledger_entry_for_raw_transaction(sender, instance, **kwargs):
    try:
        if instance.ledger_entry:
            instance.ledger_entry.delete()
    except:
        pass


@receiver(post_delete, sender=LedgerAndRawDebit)
def delete_ledger_entry_for_raw_debit(sender, instance, **kwargs):
    try:
        if instance.ledger_entry:
            instance.ledger_entry.delete()
    except:
        pass


@receiver(post_delete, sender=LedgerAndPayment)
def delete_ledger_entry_for_payment(sender, instance, **kwargs):
    try:
        if instance.ledger_entry:
            instance.ledger_entry.delete()
    except:
        pass
