from rest_framework import serializers

from .models import DyingUnit


class DyingUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = DyingUnit
        fields = ["id", "name"]
        read_only_fields = ["id"]

    def validate(self, data):
        branch = self.context["request"].branch
        if DyingUnit.objects.filter(name=data["name"], branch=branch).exists():
            raise serializers.ValidationError("Dying already exists")
        return data

    def create(self, validated_data):
        validated_data["branch"] = self.context["request"].branch
        return super().create(validated_data)
