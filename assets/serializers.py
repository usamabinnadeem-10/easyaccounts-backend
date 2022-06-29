from datetime import datetime

from ledgers.models import Ledger
from rest_framework import serializers, status

from .choices import AssetStatusChoices
from .models import Asset


class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = ["id", "date", "name", "value", "status", "type", "sold_value"]
        read_only_fields = ["id"]

    def validate(self, data):
        if data["status"] == AssetStatusChoices.SOLD:
            if data["sold_value"] is None or data["sold_value"] <= 0.0:
                raise serializers.ValidationError(
                    "Add a selling price for the asset", status.HTTP_400_BAD_REQUEST
                )
        else:
            data["sold_value"] = None

        return data

    def create(self, validated_data):
        validated_data["branch"] = self.context["request"].branch
        instance = super().create(validated_data)
        return instance
