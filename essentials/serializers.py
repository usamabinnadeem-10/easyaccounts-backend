from rest_framework import serializers

from .models import *
from ledgers.models import Ledger

from datetime import date


class PersonSerializer(serializers.ModelSerializer):

    opening_balance_date = serializers.DateField(default=date.today, write_only=True)
    nature = serializers.CharField(write_only=True)

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
            "nature",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        opening_balance_date = validated_data.pop("opening_balance_date")
        nature = validated_data.pop("nature")
        data_for_person = validated_data
        data_for_person["opening_balance"] = (
            abs(data_for_person["opening_balance"])
            if nature == "C"
            else -abs(data_for_person["opening_balance"])
        )
        data_for_person["branch"] = self.context["request"].branch
        person = Person.objects.create(**data_for_person)
        Ledger.objects.create(
            person=person,
            nature=nature,
            date=opening_balance_date,
            detail="Opening Balance",
            amount=abs(person.opening_balance),
            branch=person.branch,
        )
        return person


class AccountTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountType
        fields = ["id", "name", "opening_balance"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        validated_data["branch"] = self.context["request"].branch
        instance = super().create(validated_data)
        return instance


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ["id", "name", "address"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        validated_data["branch"] = self.context["request"].branch
        instance = instance = super().create(validated_data)
        return instance


class ProductSerializer(serializers.ModelSerializer):

    yards_per_piece = serializers.FloatField(write_only=True)
    warehouse = serializers.UUIDField(write_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "opening_stock",
            "opening_stock_rate",
            "yards_per_piece",
            "warehouse",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):

        yards_per_piece = validated_data.pop("yards_per_piece")
        warehouse = validated_data.pop("warehouse")
        warehouse = Warehouse.objects.get(id=warehouse)

        validated_data["branch"] = self.context["request"].branch
        product = Product.objects.create(**validated_data)

        if validated_data["opening_stock"] and validated_data["opening_stock_rate"]:
            Stock.objects.create(
                **{
                    "product": product,
                    "warehouse": warehouse,
                    "stock_quantity": product.opening_stock,
                    "yards_per_piece": yards_per_piece,
                    "branch": product.branch,
                }
            )
        return product


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

    def create(self, validated_data):
        validated_data["branch"] = self.context["request"].branch
        instance = super().create(validated_data)
        return instance


class AreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = ["id", "name", "city"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        validated_data["branch"] = self.context["request"].branch
        instance = super().create(validated_data)
        return instance
