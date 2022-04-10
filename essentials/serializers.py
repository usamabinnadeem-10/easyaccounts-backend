from datetime import date

from ledgers.models import Ledger
from rest_framework import serializers, status
from transactions.models import TransactionDetail

from .models import *


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
    class Meta:
        model = Product
        fields = ["id", "name", "category", "minimum_rate"]
        read_only_fields = ["id"]

    def validate(self, data):
        branch = self.context["request"].branch
        if Product.objects.filter(
            branch=branch, name=data["name"], category=data["category"]
        ).exists():
            raise serializers.ValidationError(
                "Product exists", status.HTTP_400_BAD_REQUEST
            )
        return data

    def create(self, validated_data):

        validated_data["branch"] = self.context["request"].branch
        product = Product.objects.create(**validated_data)
        return product


class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ["id", "name"]
        read_only_fields = ["id"]

    def validate(self, data):
        if ProductCategory.objects.filter(
            name=data["name"], branch=self.context["request"].branch
        ).exists():
            raise serializers.ValidationError(
                "Category already exists", status.HTTP_400_BAD_REQUEST
            )
        return data

    def create(self, validated_data):

        validated_data["branch"] = self.context["request"].branch
        category = ProductCategory.objects.create(**validated_data)
        return category


class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = [
            "id",
            "product",
            "warehouse",
            "stock_quantity",
            "yards_per_piece",
            "opening_stock",
            "opening_stock_rate",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        validated_data["branch"] = self.context["request"].branch
        if Stock.objects.filter(
            product=validated_data["product"],
            warehouse=validated_data["warehouse"],
            yards_per_piece=validated_data["yards_per_piece"],
            branch=validated_data["branch"],
        ).exists():
            raise serializers.ValidationError(
                "Opening stock exists for this product", status.HTTP_400_BAD_REQUEST
            )
        if TransactionDetail.is_rate_invalid(
            "D", validated_data["product"], validated_data["opening_stock_rate"]
        ):
            raise serializers.ValidationError(
                "Rate too low for this product", status.HTTP_400_BAD_REQUEST
            )
        validated_data["stock_quantity"] = validated_data["opening_stock"]
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
