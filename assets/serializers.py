from datetime import datetime

from ledgers.models import Ledger
from rest_framework import serializers, status

from .models import Asset


class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = [
            "id",
            "date",
            "name",
            "value",
            "status",
            "type",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        validated_data["branch"] = self.context["request"].branch
        instance = super().create(validated_data)
        return instance
