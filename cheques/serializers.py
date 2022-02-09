from rest_framework import serializers

from .models import *
from ledgers.models import Ledger
from essentials.models import LinkedAccount


class ChequeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cheque
        fields = "__all__"
        read_only_fields = ["id", "serial"]


class ChequeHistorySerializer(serializers.ModelSerializer):

    return_cheque = ChequeSerializer(required=False)

    class Meta:
        model = ChequeHistory
        fields = ["id", "cheque", "account_type", "amount", "return_cheque"]
        read_only_fields = ["id", "return_cheque"]

    def validate(self, data):
        try:
            cheque_account = LinkedAccount.objects.get(name="cheque_account")
        except:
            raise serializers.ValidationError(
                "Please create a cheque account first", 400
            )
        if data["account_type"] == cheque_account.account:
            raise serializers.ValidationError(
                "Account type can not be cheque account", 400
            )
        return data


class ListChequeHistorySerializer(serializers.ModelSerializer):

    cheque_history = ChequeHistorySerializer(many=True)

    class Meta:
        model = Cheque
        fields = [
            "id",
            "date",
            "serial",
            "bank",
            "due_date",
            "is_passed",
            "amount",
            "cheque_number",
            "cheque_history",
            "person",
        ]
        read_only_fields = ["id", "serial"]


class CreateChequeEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Cheque
        fields = [
            "id",
            "date",
            "serial",
            "bank",
            "due_date",
            "is_passed",
            "person",
            "amount",
            "cheque_number",
        ]
        read_only_fields = ["id", "serial"]

    def create(self, validated_data):
        try:
            cheque_linked_account = LinkedAccount.objects.get(name="cheque_account")
        except:
            raise serializers.ValidationError("Please create a cheque account", 400)
        data_for_cheque = {**validated_data, "serial": Cheque.get_next_serial()}
        cheque_obj = Cheque.objects.create(**data_for_cheque)
        data_for_ledger = {
            "date": cheque_obj.date,
            "amount": cheque_obj.amount,
            "nature": "C",
            "person": cheque_obj.person,
            "account_type": cheque_linked_account.account,
            "cheque": cheque_obj,
            "detail": (
                f"""{cheque_obj.get_bank_display()} -- {cheque_obj.cheque_number} / due date : {cheque_obj.due_date}"""
            ),
        }

        Ledger.objects.create(**data_for_ledger)

        return cheque_obj


class ChequeHistoryWithChequeSerializer(serializers.ModelSerializer):

    cheque_data = ChequeSerializer()

    class Meta:
        model = ChequeHistory
        fields = [
            "id",
            "cheque",
            "account_type",
            "amount",
            "return_cheque",
            "cheque_data",
        ]
        read_only_fields = ["id", "account_type", "return_cheque", "amount"]

    def create(self, validated_data):
        data_for_cheque = validated_data.pop("cheque_data")
        cheque_obj = Cheque.objects.create(
            **{**data_for_cheque, "serial": Cheque.get_next_serial()}
        )
        try:
            cheque_account = LinkedAccount.objects.get(name="cheque_account")
        except:
            raise serializers.ValidationError(
                "Please create a cheque account first", 400
            )

        data_for_cheque_history = {
            **validated_data,
            "amount": cheque_obj.amount,
            "account_type": cheque_account.account,
            "return_cheque": cheque_obj,
        }
        ChequeHistory.objects.create(**data_for_cheque_history)

        validated_data["cheque_data"] = cheque_obj
        return validated_data
