from rest_framework import serializers

from django.db.models import Sum

from .models import ExternalChequeHistory
from .choices import ChequeStatusChoices
from .constants import CHEQUE_ACCOUNT

from ledgers.models import Ledger
from essentials.models import LinkedAccount


def get_cheque_account():
    """get cheque account"""
    try:
        return LinkedAccount.objects.get(name=CHEQUE_ACCOUNT)
    except:
        raise serializers.ValidationError("Please create a cheque account first", 400)


def is_valid_history_entry(data, parent_cheque):
    """checks if amount is legal when history is created"""
    remaining_amount = ExternalChequeHistory.get_remaining_amount(
        parent_cheque, data["cheque_account"]
    )
    total_amount_received = ExternalChequeHistory.get_amount_received(data["cheque"])
    error = ""
    if remaining_amount >= data["amount"]:
        if parent_cheque.amount - total_amount_received >= data["amount"]:
            return True
        else:
            error = f"Remaining amount = {parent_cheque.amount - total_amount_received}, you entered {data['amount']}"
    else:
        error = (
            f"Remaining cheque value = {remaining_amount}, you entered {data['amount']}"
        )
    raise serializers.ValidationError(
        error,
        400,
    )


def get_parent_cheque(validated_data):
    previous_history = ExternalChequeHistory.objects.filter(
        return_cheque=validated_data["cheque"], branch=validated_data["branch"]
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
    return ExternalChequeHistory.objects.filter(cheque=cheque, branch=branch).exists()


def is_transferred(cheque):
    """check if this cheque has already been transferred"""
    return cheque.status == ChequeStatusChoices.TRANSFERRED


def get_cheque_account(branch):
    """get cheque account"""
    try:
        return LinkedAccount.objects.get(name=CHEQUE_ACCOUNT, branch=branch)
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
    message = ""
    if is_transfer and nature == "C":
        message = "Cheque return -- "
    elif is_transfer and nature == "D":
        message = "Cheque transfer -- "
    cheque_linked_account = get_cheque_account(cheque_obj.branch)
    data_for_ledger = {
        "branch": cheque_obj.branch,
        "date": cheque_obj.date,
        "amount": cheque_obj.amount,
        "nature": nature,
        "person": transfer_to if is_transfer else cheque_obj.person,
        "account_type": cheque_linked_account.account,
        "detail": (
            f"""{message}{cheque_obj.get_bank_display()} -- {cheque_obj.cheque_number} / due date : {cheque_obj.due_date} / serial ({cheque_obj.serial})"""
        ),
    }

    cheque_type = kwargs.get("cheque_type")
    if cheque_type == "personal":
        data_for_ledger.update({"personal_cheque": cheque_obj})
    else:
        data_for_ledger.update({"external_cheque": cheque_obj})

    Ledger.objects.create(**data_for_ledger)
