from rest_framework import serializers

from cheques.utils import get_cheque_account
from logs.choices import ActivityCategory, ActivityTypes
from logs.models import Log

from .models import Ledger, LedgerAndDetail


class LedgerSerializer(serializers.ModelSerializer):
    detail = serializers.SerializerMethodField(read_only=True)
    serial = serializers.SerializerMethodField(read_only=True)
    ledger_detail_id = serializers.SerializerMethodField(read_only=True)
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
            "ledger_detail_id",
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
        elif obj.ledger_detail.exists():
            return obj.ledger_detail.first().detail
        elif obj.ledger_raw_transaction.exists():
            return obj.ledger_raw_transaction.first().get_raw_transaction_string()

    def get_serial(self, obj):
        """serial number"""
        if obj.ledger_transaction.exists():
            return f"{obj.ledger_transaction.first().transaction.get_computer_and_bill_serial()} "
        elif obj.ledger_external_cheque.exists():
            return f"CHE-{obj.ledger_external_cheque.first().external_cheque.serial}"
        elif obj.ledger_personal_cheque.exists():
            return f"CHP-{obj.ledger_personal_cheque.first().personal_cheque.serial}"
        elif obj.ledger_payment.exists():
            return f"P-{obj.ledger_payment.first().payment.serial} {obj.ledger_payment.first().payment.detail}"
        else:
            return "---"

    def get_ledger_detail_id(self, obj):
        if obj.ledger_detail.exists():
            return obj.ledger_detail.first().id
        return None


class LedgerSerializerForCreation(serializers.ModelSerializer):
    class Meta:
        model = Ledger
        fields = [
            "id",
            "person",
            "date",
            "amount",
            "nature",
            "account_type",
        ]
        read_only_fields = ["id"]


class LedgerAndDetailSerializer(serializers.ModelSerializer):
    ledger_entry = LedgerSerializerForCreation()

    class Meta:
        model = LedgerAndDetail
        fields = ["id", "ledger_entry", "detail"]
        read_only_fields = ["id"]

    def validate(self, data):
        curr_account = data["ledger_entry"].get("account_type", None)
        if curr_account:
            if (
                get_cheque_account(self.context["request"].branch).account.id
                == curr_account.id
            ):
                raise serializers.ValidationError("Please use another account type", 400)
        return data

    def create(self, validated_data):
        detail = validated_data.pop("detail")
        ledger_entry = Ledger.objects.create(**validated_data["ledger_entry"])
        LedgerAndDetail.objects.create(ledger_entry=ledger_entry, detail=detail)
        validated_data["detail"] = detail

        log_string = (
            f"""{ledger_entry.amount}/= {ledger_entry.get_nature_display()}"""
            f""" for {ledger_entry.person.name} {ledger_entry.date}"""
        )

        Log.create_log(
            ActivityTypes.CREATED,
            ActivityCategory.LEDGER_ENTRY,
            log_string,
            self.context["request"],
        )

        return validated_data

    def update(self, instance, validated_data):
        detail = validated_data.pop("detail")
        ledger_entry = Ledger.objects.get(id=instance.ledger_entry.id)
        for attr, value in validated_data["ledger_entry"].items():
            setattr(ledger_entry, attr, value)
        ledger_entry.save()
        instance.detail = detail
        instance.save()
        validated_data["detail"] = detail

        log_string = (
            f"""{instance.ledger_entry.amount}/= {instance.ledger_entry.get_nature_display()}"""
            f""" for {instance.ledger_entry.person.name} {instance.ledger_entry.date} --> \n"""
            f"""{ledger_entry.amount}/= {ledger_entry.get_nature_display()}"""
            f""" for {ledger_entry.person.name} {ledger_entry.date}"""
        )

        Log.create_log(
            ActivityTypes.EDITED,
            ActivityCategory.LEDGER_ENTRY,
            log_string,
            self.context["request"],
        )

        return validated_data
