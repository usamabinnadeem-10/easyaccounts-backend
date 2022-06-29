from datetime import datetime

from essentials.models import LinkedAccount
from rest_framework import serializers

from .constants import CHEQUE_ACCOUNT


def convert_date_to_datetime(date, return_none=False):
    """get datetime format"""
    return (
        datetime.strptime(f"{date}", "%Y-%m-%d %H:%M:%S")
        if date
        else None
        if return_none
        else datetime.now()
    )


def is_string_a_number(s):
    """Returns True is string is a number."""
    return s.replace(".", "", 1).isdigit()


def convert_qp_dict_to_qp(qpDict):
    dict = {}
    for key, value in qpDict.items():
        val = value[0]
        if is_string_a_number(val):
            dict[key] = float(val)
        else:
            dict[key] = val
    return dict


def get_cheque_account(branch):
    """get cheque account"""
    try:
        return LinkedAccount.objects.get(name=CHEQUE_ACCOUNT, account__branch=branch)
    except:
        raise serializers.ValidationError("Please create a cheque account first", 400)
