from django.db import models
from django.db.models import fields
from rest_framework import serializers

from .models import *


class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = ["name", "person_type", "business_name"]


class AccountTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountType
        fields = ["name", "balance"]


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ["name", "address"]


class ProductColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductColor
        fields = ["id", "color_name"]
        read_only_fields = ["id"]


class ProductHeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductHead
        fields = ["id", "head_name"]
        read_only_fields = ["id"]


class ProductSerializer(serializers.ModelSerializer):

    color_name = serializers.CharField(
        source="product_color.color_name", read_only=True
    )
    head_name = serializers.CharField(source="product_head.head_name", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "unit",
            "current_quantity",
            "product_head",
            "product_color",
            "color_name",
            "head_name",
        ]
        read_only_fields = ["id"]


class CreateProductSerializer(serializers.Serializer):

    product_data = ProductSerializer(write_only=True)
    color_data = ProductColorSerializer(write_only=True)

    def create(self, validated_data):
        product_color = ProductColor.objects.create(
            color_name=validated_data["color_data"]["color_name"]
        )
        Product.objects.create(
            product_head=validated_data["product_data"]["product_head"],
            product_color=product_color,
            unit=validated_data["product_data"]["unit"],
        )
        return validated_data
