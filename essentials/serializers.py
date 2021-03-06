from datetime import datetime

from ledgers.models import Ledger, LedgerAndDetail
from logs.choices import ActivityCategory, ActivityTypes
from logs.models import Log
from rest_framework import serializers, status

from .models import *


class CreateLogEntry:
    def create_log(self, category, detail, request):
        Log.create_log(
            ActivityTypes.CREATED,
            category,
            detail,
            request,
        )


class PersonSerializer(CreateLogEntry, serializers.ModelSerializer):

    category = ActivityCategory.PERSON
    opening_balance = serializers.FloatField(default=0.0, write_only=True)
    opening_balance_date = serializers.DateTimeField(
        default=datetime.now, write_only=True
    )
    nature = serializers.CharField(write_only=True)

    class Meta:
        model = Person
        fields = [
            "id",
            "name",
            "person_type",
            "address",
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
        opening_balance = validated_data.pop("opening_balance")
        validated_data["branch"] = self.context["request"].branch
        person = Person.objects.create(**validated_data)

        # self.create_log(
        #     self.category,
        #     f'{person.get_person_type_display()} "{person.name}" with opening balance {person.opening_balance}',
        #     request,
        # )
        if opening_balance != 0:
            ledger_entry = Ledger.objects.create(
                person=person,
                nature=nature,
                date=opening_balance_date,
                amount=abs(float(opening_balance)),
            )
            LedgerAndDetail.objects.create(
                ledger_entry=ledger_entry, detail="Opening Balance"
            )
        return person


class AccountTypeSerializer(CreateLogEntry, serializers.ModelSerializer):

    category = ActivityCategory.ACCOUNT_TYPE

    class Meta:
        model = AccountType
        fields = ["id", "name", "opening_balance"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        request = self.context["request"]
        validated_data["branch"] = request.branch
        instance = super().create(validated_data)
        # self.create_log(
        #     self.category,
        #     f"{instance.name} with opening balance {instance.opening_balance}",
        #     request,
        # )
        return instance


class WarehouseSerializer(CreateLogEntry, serializers.ModelSerializer):

    category = ActivityCategory.WAREHOUSE

    class Meta:
        model = Warehouse
        fields = ["id", "name"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        request = self.context["request"]
        validated_data["branch"] = request.branch
        instance = instance = super().create(validated_data)
        # self.create_log(
        #     self.category,
        #     f"{instance.name} with opening balance {instance.opening_balance}",
        #     request,
        # )
        return instance


class ProductSerializer(CreateLogEntry, serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "category"]
        read_only_fields = ["id"]

    def validate(self, data):
        request = self.context["request"]
        branch = request.branch
        if Product.objects.filter(
            category__branch=branch, name=data["name"], category=data["category"]
        ).exists():
            raise serializers.ValidationError(
                "Product exists", status.HTTP_400_BAD_REQUEST
            )
        return data

    def create(self, validated_data):
        product = Product.objects.create(**validated_data)
        return product


class ProductCategorySerializer(CreateLogEntry, serializers.ModelSerializer):
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
        request = self.context["request"]
        validated_data["branch"] = request.branch
        category = ProductCategory.objects.create(**validated_data)
        return category


class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = [
            "id",
            "product",
            "warehouse",
            "yards_per_piece",
            "opening_stock",
            "opening_stock_rate",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        if Stock.objects.filter(
            product=validated_data["product"],
            warehouse=validated_data["warehouse"],
            yards_per_piece=validated_data["yards_per_piece"],
        ).exists():
            raise serializers.ValidationError(
                "Opening stock exists for this product", status.HTTP_400_BAD_REQUEST
            )
        instance = super().create(validated_data)
        return instance


class AreaSerializer(CreateLogEntry, serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = ["id", "name"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        validated_data["branch"] = self.context["request"].branch
        instance = super().create(validated_data)
        return instance
