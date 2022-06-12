from core.utils import convert_date_to_datetime
from essentials.choices import LinkedAccountChoices
from essentials.models import LinkedAccount
from ledgers.models import Ledger, LedgerAndExternalCheque, LedgerAndPersonalCheque
from rest_framework import serializers

from .choices import ChequeStatusChoices
from .models import ExternalChequeHistory

CHEQUE_ACCOUNT = LinkedAccountChoices.CHEQUE_ACCOUNT


def is_valid_history_entry(data, parent_cheque):
    """Checks if amount is legal when history is created. Disregards hard cash"""
    error = ""
    total_amount_received = ExternalChequeHistory.get_amount_received(
        data["cheque"], data["branch"]
    )
    if total_amount_received == data["cheque"].amount:
        error = f"All amounts received against this cheque. Please check children cheques"
    elif (data["cheque"].amount - abs(total_amount_received)) - data["amount"] < 0:
        error = f"Remaining amount = {data['cheque'].amount - total_amount_received}"

    if error:
        raise serializers.ValidationError(
            error,
            400,
        )


def get_parent_cheque(validated_data):
    """Returns parent cheque and validates the history entry"""
    previous_history = ExternalChequeHistory.objects.filter(
        return_cheque=validated_data["cheque"],
        parent_cheque__person__branch=validated_data["branch"],
    )
    parent = None
    if previous_history.exists():
        parent = previous_history[0].parent_cheque
    else:
        parent = validated_data["cheque"]
    is_valid_history_entry(validated_data, parent)
    return parent


def has_history(cheque, branch):
    """check if this cheque has a history"""
    return ExternalChequeHistory.objects.filter(
        cheque=cheque, parent_cheque__person__branch=branch
    ).exists()


def is_transferred(cheque):
    """check if this cheque has already been transferred"""
    return cheque.status == ChequeStatusChoices.TRANSFERRED


def get_cheque_account(branch):
    """get cheque account"""
    try:
        return LinkedAccount.objects.get(name=CHEQUE_ACCOUNT, account__branch=branch)
    except:
        raise serializers.ValidationError("Please create a cheque account first", 400)


def is_not_cheque_account(account_type, branch):
    """raise error if it's a cheque account"""
    cheque_account = get_cheque_account(branch).account
    if cheque_account == account_type:
        raise serializers.ValidationError("Please select another account type", 400)


def create_ledger_entry_for_cheque(
    cheque_obj, nature="C", is_transfer=False, transfer_to=None, **kwargs
):
    cheque_type = kwargs.get("cheque_type")
    message = ""
    if is_transfer and nature == "C":
        message = "Cheque return -- "
    elif is_transfer and nature == "D":
        message = "Cheque transfer -- "
    cheque_linked_account = get_cheque_account(cheque_obj.person.branch)

    data_for_ledger = {
        "date": convert_date_to_datetime(kwargs.get("date", None), True)
        or cheque_obj.date,
        "amount": cheque_obj.amount,
        "nature": nature,
        "person": transfer_to if is_transfer else cheque_obj.person,
        "account_type": cheque_linked_account.account,
    }

    ledger_entry = Ledger.objects.create(**data_for_ledger)

    if cheque_type == "personal":
        LedgerAndPersonalCheque.objects.create(
            ledger_entry=ledger_entry, personal_cheque=cheque_obj
        )
    else:
        LedgerAndExternalCheque.objects.create(
            ledger_entry=ledger_entry, external_cheque=cheque_obj
        )
