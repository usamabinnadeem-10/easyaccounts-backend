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
    instances = None
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
            self.instances = obj.ledger_transaction.all()
            self.instance_type = INSTANCE_TYPES["T"]
        elif obj.ledger_external_cheque.exists():
            self.instances = obj.ledger_external_cheque.all()
            self.instance_type = INSTANCE_TYPES["EC"]
        elif obj.ledger_personal_cheque.exists():
            self.instances = obj.ledger_personal_cheque.all()
            self.instance_type = INSTANCE_TYPES["PC"]
        elif obj.ledger_payment.exists():
            self.instances = obj.ledger_payment.all()
            self.instance_type = INSTANCE_TYPES["P"]

    def set_instances(self, obj):
        """check if self.instance is None and set the property"""
        print(self.instances)
        if self.instances is None:
            self._set_instances(obj)
        print(self.instances)

    def get_detail(self, obj):
        """create ledger detail"""
        self.set_instances(obj)
        string = ""
        nature = obj.nature
        if self.instance_type == INSTANCE_TYPES["T"]:
            string = Transaction.get_transaction_string(
                self.instances, nature, obj.account_type
            )
        elif self.instance_type == INSTANCE_TYPES["EC"]:
            string = ExternalCheque.get_transaction_string(self.instances, "external")
        elif self.instance_type == INSTANCE_TYPES["PC"]:
            string = PersonalCheque.get_transaction_string(self.instances, "personal")
        elif self.instance_type == INSTANCE_TYPES["P"]:
            string = Payment.get_transaction_string(self.instances)

        return string

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
