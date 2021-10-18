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
        fields = ["name"]


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
    class Meta:
        model = Product
        fields = ["id", "unit"]
        read_only_fields = ["id"]


class CreateProductSerializer(serializers.Serializer):

    product_data = ProductSerializer(write_only=True)
    head_data = ProductHeadSerializer(write_only=True)
    color_data = ProductColorSerializer(write_only=True)

    def create(self, validated_data):
        product_color = ProductColor.objects.create(
            color_name=validated_data["color_data"]["color_name"]
        )
        product_head = ProductHead.objects.create(
            head_name=validated_data["head_data"]["head_name"]
        )
        Product.objects.create(
            product_head=product_head,
            product_color=product_color,
            unit=validated_data["product_data"]["unit"],
        )
        return {}
