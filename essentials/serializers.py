from django.db import models
from django.db.models import fields
from rest_framework import serializers

from .models import *


class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = ["id", "name", "person_type", "business_name"]
        read_only_fields = ["id"]


class AccountTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountType
        fields = ["id", "name"]
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
            "stock_quantity",
            "basic_unit",
        ]
        read_only_fields = ["id"]
