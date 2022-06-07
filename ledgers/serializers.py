from cheques.models import ExternalCheque, PersonalCheque
from logs.choices import ActivityCategory, ActivityTypes
from logs.models import Log
from rest_framework import serializers
from transactions.models import Transaction

from .models import *


class LedgerSerializer(serializers.ModelSerializer):

    transaction_serial = serializers.CharField(
        source="transaction.serial", read_only=True
    )
    manual_invoice_serial = serializers.IntegerField(
        source="transaction.manual_invoice_serial", read_only=True
    )
    manual_serial_type = serializers.CharField(
        source="transaction.manual_serial_type", read_only=True
    )
    detail = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Ledger
        fields = [
            "id",
            "person",
            "date",
            "amount",
            "nature",
            "account_type",
            "transaction_serial",
            "manual_invoice_serial",
            "manual_serial_type",
            "detail",
        ]
        read_only_fields = ["id", "detail"]
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
        string = ""
        nature = obj.nature
        if obj.ledger_transaction.exists():
            instances = obj.ledger_transaction.all()
            string = Transaction.get_transaction_string(
                instances, nature, obj.account_type
            )
        elif obj.ledger_external_cheque.exists():
            instances = obj.ledger_external_cheque.all()
            string = ExternalCheque.get_transaction_string(instances, "external")
        elif obj.ledger_personal_cheque.exists():
            instances = obj.ledger_personal_cheque.all()
            string = PersonalCheque.get_transaction_string(instances, "personal")

        return string
