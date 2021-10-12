from django.db import models
from django.db.models import fields
from rest_framework import serializers

from .models import *

class PersonSerializer(serializers.ModelSerializer):

    class Meta:
        model = Person
        fields = ['name', 'person_type', 'business_name']


class AccountTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = AccountType
        fields = ['name']


class WarehouseSerializer(serializers.ModelSerializer):

    class Meta:
        model = Warehouse
        fields = ['name', 'address']

class ProductVariantSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductVariant
        fields = ['id', 'name']
        read_only_fields = ['id']
class ProductSerializer(serializers.ModelSerializer):

    colors = ProductVariantSerializer(many=True)
    class Meta:
        model = Product
        fields = ['id', 'name', 'colors']
        read_only_fields = ['id']

    def create(self, validated_data):
        colors_data = validated_data.pop('colors')
        product = Product.objects.create(**validated_data)
        for color in colors_data:
            ProductVariant.objects.create(product_id=product, **color)
        return product
