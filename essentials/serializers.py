from django.db import models
from django.db.models import fields
from rest_framework import serializers

from .models import *

class AccountSerializer(serializers.ModelSerializer):

    class Meta:
        model = Account
        fields = ['name', 'account_type', 'business_name']


class WarehouseSerializer(serializers.ModelSerializer):

    class Meta:
        model = Warehouse
        fields = ['name', 'address']


class ProductSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = ['name']


class ProductVariantSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductVariant
        field = ['name']


class ParentProductSerializer(serializers.Serializer):

    product = ProductSerializer()
    product_variant = ProductVariantSerializer()


    def create(self, validated_data):
        return super().create(validated_data)
