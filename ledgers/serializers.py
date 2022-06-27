from cheques.models import ExternalCheque, PersonalCheque
from logs.choices import ActivityCategory, ActivityTypes
from logs.models import Log
from payments.models import Payment
from rest_framework import serializers
from transactions.models import Transaction

from .constants import INSTANCE_TYPES
from .models import *


class LedgerSerializer(serializers.ModelSerializer):

    detail = serializers.SerializerMethodField(read_only=True)
    serial = serializers.SerializerMethodField(read_only=True)
    instance_type = None

    class Meta:
        model = Ledger
        fields = [
            "id",
            "person",
            "date",
            "amount",
            "nature",
            "account_type",
            "detail",
            "serial",
        ]
        read_only_fields = ["id", "detail", "serial"]
        extra_kwargs = {
            "account_type": {"required": False},
            "transaction": {"required": False},
        }

    def create(self, validated_data):
        request = self.context["request"]
        validated_data["branch"] = self.context["request"].branch
        validated_data["user"] = self.context["request"].user
        instance = super().create(validated_data)
        Log.create_log(
            ActivityTypes.CREATED,
            ActivityCategory.LEDGER_ENTRY,
            f"{instance.get_nature_display()} for {instance.person.name} for amount {instance.amount}/=",
            request,
        )
        return instance

    def get_detail(self, obj):
        """create ledger detail"""
        nature = obj.nature
        if obj.ledger_transaction.exists():
            return obj.ledger_transaction.first().transaction.get_transaction_string(
                nature
            )
        elif obj.ledger_external_cheque.exists():
            return obj.ledger_external_cheque.first().external_cheque.get_ledger_string(
                "external"
            )
        elif obj.ledger_personal_cheque.exists():
            return obj.ledger_personal_cheque.first().personal_cheque.get_ledger_string(
                "personal"
            )
        elif obj.ledger_payment.exists():
            return obj.ledger_payment.first().payment.get_ledger_string()
        else:
            return "Opening Balance"

    def get_serial(self, obj):
        """serial number"""
        if obj.ledger_transaction.exists():
            return obj.ledger_transaction.first().transaction.get_computer_serial()
        elif obj.ledger_external_cheque.exists():
            return f"CH-E : {obj.ledger_external_cheque.first().external_cheque.serial}"
        elif obj.ledger_personal_cheque.exists():
            return f"CH-P : {obj.ledger_personal_cheque.first().personal_cheque.serial}"
        elif obj.ledger_payment.exists():
            return f"P : {obj.ledger_payment.first().payment.serial}"
