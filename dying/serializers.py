from rawtransactions.models import RawLotDetail
from rest_framework import serializers

from .models import DyingIssue, DyingIssueDetail, DyingUnit


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


class DyingIssueDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = DyingIssueDetail
        fields = [
            "id",
            "dying_lot_number",
            "quantity",
            "actual_gazaana",
            "expected_gazaana",
            "formula",
        ]
        read_only_fields = ["id"]


class DyingIssueSerializer(serializers.ModelSerializer):

    auto_issued_detail = serializers.SerializerMethodField(allow_null=True)
    dying_issue_details = DyingIssueDetailSerializer(many=True)

    class Meta:
        model = DyingIssue
        fields = [
            "id",
            "dying_unit",
            "lot_number",
            "dying_lot_number",
            "date",
            "dying_issue_details",
            "auto_issued_detail",
        ]
        read_only_fields = ["id", "dying_lot_number"]

    def get_auto_issued_detail(self, obj):
        if obj.lot_number.issued:
            return RawLotDetail.objects.filter(lot_number=obj.lot_number.id).values()
        else:
            return []
