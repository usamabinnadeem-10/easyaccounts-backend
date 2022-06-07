from datetime import datetime

from black import err
from core.utils import convert_date_to_datetime
from django.db.models import Sum
from essentials.choices import LinkedAccountChoices
from essentials.models import LinkedAccount
from ledgers.models import Ledger, LedgerAndExternalCheque, LedgerAndPersonalCheque
from rest_framework import serializers, status

from .choices import ChequeStatusChoices
from .models import ExternalChequeHistory

CHEQUE_ACCOUNT = LinkedAccountChoices.CHEQUE_ACCOUNT


def get_cheque_account():
    """get cheque account"""
    try:
        return LinkedAccount.objects.get(name=CHEQUE_ACCOUNT)
    except:
        raise serializers.ValidationError("Please create a cheque account first", 400)


def is_valid_history_entry(data, parent_cheque):
    """Checks if amount is legal when history is created. Disregards hard cash"""
    # remaining_amount = ExternalChequeHistory.get_remaining_amount(
    #     parent_cheque, data["cheque_account"], data["branch"]
    # )
    error = ""
    total_amount_received = ExternalChequeHistory.get_amount_received(
        data["cheque"], data["branch"]
    )
    if total_amount_received == data["cheque"].amount:
        error = f"All amounts received against this cheque. Please check children cheques"
    elif (data["cheque"].amount - abs(total_amount_received)) - data["amount"] < 0:
        error = f"Remaining amount = {data['cheque'].amount - total_amount_received}"

    # if remaining_amount >= data["amount"]:
    #     if parent_cheque.amount - total_amount_received >= data["amount"]:
    #         return True
    #     else:
    #         error = f"Remaining amount = {parent_cheque.amount - total_amount_received}, you entered {data['amount']}"
    # else:
    #     error = (
    #         f"Remaining cheque value = {remaining_amount}, you entered {data['amount']}"
    #     )
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
        "branch": cheque_obj.person.branch,
        "date": convert_date_to_datetime(kwargs.get("date", None), True)
        or cheque_obj.date,
        "amount": cheque_obj.amount,
        "nature": nature,
        "person": transfer_to if is_transfer else cheque_obj.person,
        "account_type": cheque_linked_account.account,
        # "detail": (
        #     f"""{message}{cheque_obj.get_bank_display()} -- {cheque_obj.cheque_number} / due date : {cheque_obj.due_date} / serial ({cheque_obj.serial})"""
        # ),
    }

    # extra_detail = ""

    ledger_entry = Ledger.objects.create(**data_for_ledger)

    if cheque_type == "personal":
        # data_for_ledger.update({"personal_cheque": cheque_obj})
        LedgerAndPersonalCheque.objects.create(
            ledger_entry=ledger_entry, personal_cheque=cheque_obj
        )
        # if nature == "C":
        #     extra_detail = "Personal cheque return -- "
        # else:
        #     extra_detail = "Personal cheque issue -- "
        # data_for_ledger.update({"detail": f"{extra_detail}{data_for_ledger['detail']}"})
    else:
        LedgerAndExternalCheque.objects.create(
            ledger_entry=ledger_entry, external_cheque=cheque_obj
        )
        # data_for_ledger.update({"external_cheque": cheque_obj})
