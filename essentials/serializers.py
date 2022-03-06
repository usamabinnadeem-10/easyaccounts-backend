from rest_framework import serializers

from .models import *
from ledgers.models import Ledger

from datetime import date


class PersonSerializer(serializers.ModelSerializer):

    opening_balance_date = serializers.DateField(default=date.today, write_only=True)

    class Meta:
        model = Person
        fields = [
            "id",
            "name",
            "person_type",
            "business_name",
            "address",
            "city",
            "phone_number",
            "area",
            "opening_balance",
            "opening_balance_date",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        opening_balance_date = validated_data.pop("opening_balance_date")
        person = Person.objects.create(**validated_data)
        Ledger.objects.create(
            person=person,
            nature="C" if person.opening_balance > 0 else "D",
            date=opening_balance_date,
            detail="Opening Balance",
            amount=abs(person.opening_balance),
        )
        return person


class AccountTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountType
        fields = ["id", "name", "opening_balance"]
        read_only_fields = ["id"]


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ["id", "name", "address"]
        read_only_fields = ["id"]


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "id",
            "si_unit",
            "name",
            "basic_unit",
        ]
        read_only_fields = ["id"]


class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = [
            "id",
            "product",
            "warehouse",
            "stock_quantity",
            "yards_per_piece",
        ]
        read_only_fields = ["id"]


class AreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = ["id", "name", "city"]
        read_only_fields = ["id"]
