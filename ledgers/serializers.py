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

    def _set_instances(self, obj):
        """set related instances of the current object being serialized"""
        if obj.ledger_transaction.exists():
            self.instance_type = INSTANCE_TYPES["T"]
        elif obj.ledger_external_cheque.exists():
            self.instance_type = INSTANCE_TYPES["EC"]
        elif obj.ledger_personal_cheque.exists():
            self.instance_type = INSTANCE_TYPES["PC"]
        elif obj.ledger_payment.exists():
            self.instance_type = INSTANCE_TYPES["P"]

    def set_instances(self, obj):
        """check if self.instance is None and set the property"""
        self._set_instances(obj)

    def get_detail(self, obj):
        """create ledger detail"""
        self.set_instances(obj)
        nature = obj.nature
        if self.instance_type == INSTANCE_TYPES["T"]:
            return obj.ledger_transaction.first().transaction.get_transaction_string(
                nature
            )
        elif self.instance_type == INSTANCE_TYPES["EC"]:
            return obj.ledger_external_cheque.first().external_cheque.get_ledger_string(
                "external"
            )
        elif self.instance_type == INSTANCE_TYPES["PC"]:
            return obj.ledger_personal_cheque.first().personal_cheque.get_ledger_string(
                "personal"
            )
        elif self.instance_type == INSTANCE_TYPES["P"]:
            return obj.ledger_payment.first().payment.get_ledger_string()

    def get_serial(self, obj):
        """serial number"""
        if self.instance_type == INSTANCE_TYPES["T"]:
            return obj.ledger_transaction.first().transaction.get_computer_serial()
        elif self.instance_type == INSTANCE_TYPES["EC"]:
            return f"CH-E : {obj.ledger_external_cheque.first().external_cheque.serial}"
        elif self.instance_type == INSTANCE_TYPES["PC"]:
            return f"CH-P : {obj.ledger_personal_cheque.first().personal_cheque.serial}"
        elif self.instance_type == INSTANCE_TYPES["P"]:
            return f"P : {obj.ledger_payment.first().payment.serial}"
