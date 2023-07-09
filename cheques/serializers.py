from datetime import datetime

from django.shortcuts import get_object_or_404
from rest_framework import serializers

from essentials.models import Person
from logs.choices import ActivityCategory, ActivityTypes
from logs.models import Log

from .choices import ChequeStatusChoices, PersonalChequeStatusChoices
from .models import (
    ExternalCheque,
    ExternalChequeHistory,
    ExternalChequeTransfer,
    PersonalCheque,
)
from .utils import (
    create_ledger_entry_for_cheque,
    get_cheque_account,
    get_parent_cheque,
    has_history,
    is_not_cheque_account,
    is_transferred,
)

# from ledgers.models import Ledger
# from essentials.models import LinkedAccount, AccountType


CHEQUE_ACCOUNT = "cheque_account"


class ExternalChequeSerializer(serializers.ModelSerializer):
    transferred_to = serializers.SerializerMethodField()

    class Meta:
        model = ExternalCheque
        fields = [
            "id",
            "serial",
            "cheque_number",
            "bank",
            "date",
            "due_date",
            "amount",
            "person",
            "status",
            "is_passed_with_history",
            "transferred_to",
        ]
        read_only_fields = ["id", "serial", "person", "transferred_to"]

    def get_transferred_to(self, obj):
        transfer = ExternalChequeTransfer.objects.filter(cheque=obj)
        if transfer.exists():
            return transfer[0].person.name
        return None


class ShortExternalChequeHistorySerializer(serializers.ModelSerializer):
    serial = serializers.IntegerField(source="parent_cheque.serial")
    cheque_number = serializers.CharField(source="parent_cheque.cheque_number")
    person = serializers.UUIDField(source="parent_cheque.person.id")

    class Meta:
        model = ExternalChequeHistory
        fields = [
            "id",
            "serial",
            "account_type",
            "amount",
            "date",
            "cheque_number",
            "person",
        ]


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
        branch = self.context["request"].branch
        cheque_account = get_cheque_account(branch)
        if data["account_type"] == cheque_account.account:
            raise serializers.ValidationError(
                "Account type can not be cheque account", 400
            )
        if is_transferred(data["cheque"]):
            raise serializers.ValidationError("Cheque has already been transferred", 400)
        return data

    def create(self, validated_data):
        branch = self.context["request"].branch
        user = self.context["request"].user
        cheque_account = get_cheque_account(branch)
        parent_cheque = get_parent_cheque(
            {
                **validated_data,
                "cheque_account": cheque_account.account,
                "branch": branch,
            }
        )

        external_cheque = ExternalChequeHistory.objects.create(
            **{
                **validated_data,
                "parent_cheque": parent_cheque,
                "user": user,
            }
        )

        Log.create_log(
            ActivityTypes.CREATED,
            ActivityCategory.EXTERNAL_CHEQUE_HISTORY,
            external_cheque.get_log_string(),
            self.context["request"],
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
        branch = self.context["request"].branch
        user = self.context["request"].user
        data_for_cheque = {
            **validated_data,
            "serial": ExternalCheque.get_next_serial("serial", person__branch=branch),
            "user": user,
        }
        external_cheque_obj = ExternalCheque.objects.create(**data_for_cheque)
        create_ledger_entry_for_cheque(external_cheque_obj)

        log_string = (
            f"CHE-{external_cheque_obj.serial} " + external_cheque_obj.get_log_string()
        )

        Log.create_log(
            ActivityTypes.CREATED,
            ActivityCategory.EXTERNAL_CHEQUE,
            log_string,
            self.context["request"],
        )

        return external_cheque_obj


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
            raise serializers.ValidationError("Cheque has already been transferred", 400)
        return data

    def create(self, validated_data):
        branch = self.context["request"].branch
        user = self.context["request"].user
        branch_filter = {"branch": branch}
        data_for_cheque = validated_data.pop("cheque_data")
        cheque_obj = ExternalCheque.objects.create(
            **{
                **data_for_cheque,
                "serial": ExternalCheque.get_next_serial("serial", person__branch=branch),
                "person": validated_data["cheque"].person,
            }
        )
        cheque_account = get_cheque_account(branch)
        data_for_cheque_history = {
            **validated_data,
            "date": validated_data.get("date", None) or cheque_obj.date,
            "user": user,
            "amount": cheque_obj.amount,
            "account_type": cheque_account.account,
            "return_cheque": cheque_obj,
            "parent_cheque": get_parent_cheque(
                {
                    "cheque": validated_data["cheque"],
                    "amount": cheque_obj.amount,
                    "cheque_account": cheque_account.account,
                    **branch_filter,
                }
            ),
        }
        external_cheque_obj = ExternalChequeHistory.objects.create(
            **data_for_cheque_history
        )

        Log.create_log(
            ActivityTypes.CREATED,
            ActivityCategory.EXTERNAL_CHEQUE,
            external_cheque_obj.get_log_string(),
            self.context["request"],
        )

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
        branch = self.context["request"].branch
        cheque_account = get_cheque_account(branch).account
        return ExternalChequeHistory.get_remaining_amount(obj, cheque_account, branch)


class TransferExternalChequeSerializer(serializers.ModelSerializer):
    date = serializers.DateTimeField(default=datetime.now, write_only=True)

    class Meta:
        model = ExternalChequeTransfer
        fields = ["id", "cheque", "person", "date"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        branch = self.context["request"].branch
        user = self.context["request"].user
        cheque = validated_data["cheque"]
        date = validated_data.pop("date")
        # cheque with hisotry can not be transferred
        if has_history(cheque, branch):
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

        transfer = ExternalChequeTransfer.objects.create(**validated_data, user=user)
        create_ledger_entry_for_cheque(
            transfer.cheque, "D", True, validated_data["person"], **{"date": date}
        )

        cheque.status = ChequeStatusChoices.TRANSFERRED
        cheque.save()

        Log.create_log(
            ActivityTypes.EDITED,
            ActivityCategory.EXTERNAL_CHEQUE,
            f"CHE-{transfer.cheque.serial} transferred to {transfer.person.name}",
            self.context["request"],
        )

        return validated_data


class CompleteExternalTransferChequeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalCheque
        fields = "__all__"
        read_only_fields = ["id"]

    def update(self, instance, validated_data):
        if instance.status != ChequeStatusChoices.TRANSFERRED:
            raise serializers.ValidationError(
                f"This cheque is not transferred, it is in {instance.status} state"
            )
        instance.status = ChequeStatusChoices.COMPLETED_TRANSFER
        instance.save()

        Log.create_log(
            ActivityTypes.EDITED,
            ActivityCategory.EXTERNAL_CHEQUE,
            f"CHE-{instance.serial} transferred cheque completed",
            self.context["request"],
        )

        return instance


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
        branch = self.context["request"].branch
        user = self.context["request"].user
        is_not_cheque_account(validated_data["account_type"], branch)
        data_for_cheque = {
            **validated_data,
            "serial": PersonalCheque.get_next_serial("serial", person__branch=branch),
            "user": user,
        }
        personal_cheque = PersonalCheque.objects.create(**data_for_cheque)
        create_ledger_entry_for_cheque(
            personal_cheque, "D", **{"cheque_type": "personal"}
        )
        log_string = f"CHP-{personal_cheque.serial} " + personal_cheque.get_log_string()
        Log.create_log(
            ActivityTypes.CREATED,
            ActivityCategory.PERSONAL_CHEQUE,
            log_string,
            self.context["request"],
        )

        return validated_data


class ReturnPersonalChequeSerializer(serializers.Serializer):
    """return personal cheque from a person"""

    cheque = serializers.UUIDField()
    date = serializers.DateTimeField(write_only=True)

    def create(self, validated_data):
        branch = self.context["request"].branch
        date = validated_data.pop("date")
        cheque = get_object_or_404(
            PersonalCheque,
            id=validated_data["cheque"],
            status=PersonalChequeStatusChoices.PENDING,
            person__branch=branch,
        )
        cheque.status = PersonalChequeStatusChoices.RETURNED
        cheque.save()

        create_ledger_entry_for_cheque(
            cheque, "C", **{"cheque_type": "personal"}, **{"date": date}
        )

        Log.create_log(
            ActivityTypes.EDITED,
            ActivityCategory.PERSONAL_CHEQUE,
            f"CHP-{cheque.serial} returned back from {cheque.person.name}",
            self.context["request"],
        )

        return validated_data


class ReIssuePersonalChequeFromReturnedSerializer(serializers.Serializer):
    """issue a personal cheque from the ones that were returned"""

    cheque = serializers.UUIDField()
    person = serializers.UUIDField()
    date = serializers.DateTimeField(write_only=True)

    def create(self, validated_data):
        branch = self.context["request"].branch
        date = validated_data.pop("date")
        cheque = get_object_or_404(
            PersonalCheque,
            id=validated_data["cheque"],
            status=PersonalChequeStatusChoices.RETURNED,
            person__branch=branch,
        )
        person = get_object_or_404(Person, id=validated_data["person"], branch=branch)
        cheque.person = person
        cheque.status = PersonalChequeStatusChoices.PENDING
        cheque.save()

        create_ledger_entry_for_cheque(
            cheque, "D", **{"cheque_type": "personal"}, **{"date": date}
        )

        Log.create_log(
            ActivityTypes.EDITED,
            ActivityCategory.PERSONAL_CHEQUE,
            f"CHP-{cheque.serial} issued back to {cheque.person.name}",
            self.context["request"],
        )

        return validated_data


class PassPersonalChequeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonalCheque
        fields = ["id"]

    def update(self, instance, validated_data):
        if instance.status == PersonalChequeStatusChoices.PENDING:
            instance.status = PersonalChequeStatusChoices.CLEARED
            instance.save()

            Log.create_log(
                ActivityTypes.EDITED,
                ActivityCategory.PERSONAL_CHEQUE,
                f"CHP-{instance.serial} passed",
                self.context["request"],
            )

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

            Log.create_log(
                ActivityTypes.EDITED,
                ActivityCategory.PERSONAL_CHEQUE,
                f"CHP-{instance.serial} cancelled",
                self.context["request"],
            )

            return instance
        raise serializers.ValidationError(f"Cheque is already {instance.status}")
