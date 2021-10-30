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
            "si_unit",
            "product_head",
            "product_color",
            "color_name",
            "head_name",
            "basic_unit",
        ]
        read_only_fields = ["id"]


class CreateProductSerializer(serializers.Serializer):

    id = serializers.UUIDField(read_only=True)
    head_name = serializers.CharField(read_only=True)
    color_name = serializers.CharField(read_only=True)

    product_head = serializers.UUIDField()
    si_unit = serializers.CharField()
    basic_unit = serializers.FloatField()
    product_color = serializers.CharField()

    def create(self, validated_data):
        product_color = ProductColor.objects.create(
            color_name=validated_data["product_color"]
        )
        product_head = ProductHead.objects.get(id=validated_data["product_head"])
        product = Product.objects.create(
            product_color=product_color,
            product_head=product_head,
            si_unit=validated_data["si_unit"],
            basic_unit=validated_data["basic_unit"],
        )
        validated_data["id"] = product.id
        validated_data["product_color"] = product_color.id
        validated_data["head_name"] = product_head.head_name
        validated_data["color_name"] = product_color.color_name

        return validated_data
