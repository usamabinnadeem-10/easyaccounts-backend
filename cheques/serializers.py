from rest_framework import serializers

from django.db.models import Sum
from django.shortcuts import get_object_or_404

from essentials.models import Person

from .models import (
    ExternalCheque,
    ExternalChequeHistory,
    PersonalCheque,
    ExternalChequeTransfer,
)
from .choices import ChequeStatusChoices, PersonalChequeStatusChoices
from .utils import (
    get_cheque_account,
    get_parent_cheque,
    is_transferred,
    create_ledger_entry_for_cheque,
    has_history,
    is_not_cheque_account,
)

# from ledgers.models import Ledger
# from essentials.models import LinkedAccount, AccountType


CHEQUE_ACCOUNT = "cheque_account"


class ExternalChequeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalCheque
        fields = "__all__"
        read_only_fields = ["id", "serial", "person"]


class ExternalChequeHistorySerializer(serializers.ModelSerializer):
    """Serializer for creating cheque history"""

    return_cheque = ExternalChequeSerializer(required=False)

    class Meta:
        model = ExternalChequeHistory
        fields = [
            "id",
            "parent_cheque",
            "cheque",
            "account_type",
            "amount",
            "return_cheque",
            "date",
        ]
        read_only_fields = ["id", "return_cheque", "parent_cheque"]

    def validate(self, data):
        cheque_account = get_cheque_account()
        if data["account_type"] == cheque_account.account:
            raise serializers.ValidationError(
                "Account type can not be cheque account", 400
            )
        if is_transferred(data["cheque"]):
            raise serializers.ValidationError(
                "Cheque has already been transferred", 400
            )
        return data

    def create(self, validated_data):
        parent_cheque = get_parent_cheque(validated_data)
        external_cheque = ExternalChequeHistory.objects.create(
            **{**validated_data, "parent_cheque": parent_cheque}
        )
        return external_cheque


class CreateExternalChequeEntrySerializer(serializers.ModelSerializer):
    """Serializer for creating External Cheque"""

    class Meta:
        model = ExternalCheque
        fields = [
            "id",
            "date",
            "serial",
            "bank",
            "due_date",
            "person",
            "amount",
            "cheque_number",
            "person",
            "status",
        ]
        read_only_fields = ["id", "serial"]

    def create(self, validated_data):
        data_for_cheque = {**validated_data, "serial": ExternalCheque.get_next_serial()}
        cheque_obj = ExternalCheque.objects.create(**data_for_cheque)
        create_ledger_entry_for_cheque(cheque_obj)
        return cheque_obj


class ExternalChequeHistoryWithChequeSerializer(serializers.ModelSerializer):
    """Serializer for creating External cheque against Cheque"""

    cheque_data = ExternalChequeSerializer()

    class Meta:
        model = ExternalChequeHistory
        fields = [
            "id",
            "cheque",
            "account_type",
            "amount",
            "return_cheque",
            "cheque_data",
            "date",
        ]
        read_only_fields = ["id", "account_type", "return_cheque", "amount"]

    def validate(self, data):
        if is_transferred(data["cheque"]):
            raise serializers.ValidationError(
                "Cheque has already been transferred", 400
            )
        return data

    def create(self, validated_data):
        data_for_cheque = validated_data.pop("cheque_data")
        cheque_obj = ExternalCheque.objects.create(
            **{
                **data_for_cheque,
                "serial": ExternalCheque.get_next_serial(),
                "person": validated_data["cheque"].person,
            }
        )
        cheque_account = get_cheque_account()
        data_for_cheque_history = {
            **validated_data,
            "amount": cheque_obj.amount,
            "account_type": cheque_account.account,
            "return_cheque": cheque_obj,
            "parent_cheque": get_parent_cheque(
                {
                    "cheque": validated_data["cheque"],
                    "amount": cheque_obj.amount,
                }
            ),
        }
        ExternalChequeHistory.objects.create(**data_for_cheque_history)

        validated_data["cheque_data"] = cheque_obj
        return validated_data


class ListExternalChequeHistorySerializer(serializers.ModelSerializer):
    """Serializer for listing External cheques"""

    remaining_amount = serializers.SerializerMethodField()
    cheque_history = ExternalChequeHistorySerializer(many=True)

    class Meta:
        model = ExternalCheque
        fields = "__all__"
        read_only_fields = ["id", "serial"]

    def get_remaining_amount(self, obj):
        cheque_account = get_cheque_account().account
        return ExternalChequeHistory.get_remaining_amount(obj, cheque_account)


class TransferExternalChequeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalChequeTransfer
        fields = ["id", "cheque", "person"]
        read_only_fields = ["id"]

    def create(self, validated_data):

        cheque = validated_data["cheque"]
        # cheque with hisotry can not be transferred
        if has_history(cheque):
            raise serializers.ValidationError(
                "Cheque with history can not be transferred", 400
            )

        # make sure transfer person is not the same as current person
        if cheque.person == validated_data["person"]:
            raise serializers.ValidationError(
                "You are trying to transfer cheque to the same person it came from", 400
            )

        # cheque with status == COMPLETED can not be transferred
        if cheque.status == ChequeStatusChoices.CLEARED:
            raise serializers.ValidationError(
                "Cleared cheque can not be transferred", 400
            )

        transfer = ExternalChequeTransfer.objects.create(**validated_data)
        create_ledger_entry_for_cheque(
            transfer.cheque, "D", True, validated_data["person"]
        )

        cheque.status = ChequeStatusChoices.TRANSFERRED
        cheque.save()

        return validated_data


class IssuePersonalChequeSerializer(serializers.ModelSerializer):
    """Serializer for issuing personal cheque to a person"""

    class Meta:
        model = PersonalCheque
        fields = [
            "id",
            "serial",
            "cheque_number",
            "bank",
            "date",
            "due_date",
            "amount",
            "person",
            "account_type",
            "status",
        ]
        read_only_fields = ["id", "serial", "status"]

    def create(self, validated_data):
        is_not_cheque_account(validated_data["account_type"])
        data_for_cheque = {**validated_data, "serial": PersonalCheque.get_next_serial()}
        personal_cheque = PersonalCheque.objects.create(**data_for_cheque)
        create_ledger_entry_for_cheque(
            personal_cheque, "D", **{"cheque_type": "personal"}
        )
        return validated_data


class ReturnPersonalChequeSerializer(serializers.Serializer):
    """return personal cheque from a person"""

    cheque = serializers.UUIDField()

    def create(self, validated_data):
        cheque = get_object_or_404(
            PersonalCheque,
            id=validated_data["cheque"],
            status=PersonalChequeStatusChoices.PENDING,
        )
        cheque.status = PersonalChequeStatusChoices.RETURNED
        cheque.save()

        create_ledger_entry_for_cheque(cheque, "C", **{"cheque_type": "personal"})

        return validated_data


class ReIssuePersonalChequeFromReturnedSerializer(serializers.Serializer):
    """issue a personal cheque from the ones that were returned"""

    cheque = serializers.UUIDField()
    person = serializers.UUIDField()

    def create(self, validated_data):
        cheque = get_object_or_404(
            PersonalCheque,
            id=validated_data["cheque"],
            status=PersonalChequeStatusChoices.RETURNED,
        )
        person = get_object_or_404(Person, id=validated_data["person"])
        cheque.person = person
        cheque.status = PersonalChequeStatusChoices.PENDING
        cheque.save()

        create_ledger_entry_for_cheque(cheque, "D", **{"cheque_type": "personal"})

        return validated_data


class PassPersonalChequeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonalCheque
        fields = ["id"]

    def update(self, instance, validated_data):
        if instance.status == PersonalChequeStatusChoices.PENDING:
            instance.status = PersonalChequeStatusChoices.CLEARED
            instance.save()
            return instance
        raise serializers.ValidationError(f"Cheque is already {instance.status}")


class CancelPersonalChequeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonalCheque
        fields = ["id"]

    def update(self, instance, validated_data):
        if instance.status == PersonalChequeStatusChoices.RETURNED:
            instance.status = PersonalChequeStatusChoices.CANCELLED
            instance.save()
            return instance
        raise serializers.ValidationError(f"Cheque is already {instance.status}")
