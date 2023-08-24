from rest_framework import serializers
from rest_framework.validators import ValidationError

from rawtransactions.models import RawLotDetail
from rawtransactions.serializers import UniqueLotNumbers
from rawtransactions.utils import validate_raw_inventory

from .models import DyingIssue, DyingIssueDetail, DyingIssueLot, DyingUnit


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


class DyingIssueLotSerializer(serializers.ModelSerializer):
    auto_issued_detail = serializers.SerializerMethodField(allow_null=True)
    dying_issue_lot_number = DyingIssueDetailSerializer(many=True)

    class Meta:
        model = DyingIssueLot
        fields = [
            "id",
            "dying_lot",
            "lot_number",
            "dying_issue_lot_number",
            "auto_issued_detail",
        ]

    def get_auto_issued_detail(self, obj):
        if obj.lot_number.issued:
            return RawLotDetail.objects.filter(lot_number=obj.lot_number.id).values()
        else:
            return []


class DyingIssueSerializer(serializers.ModelSerializer):
    dying_issue_lot = DyingIssueLotSerializer(many=True)

    class Meta:
        model = DyingIssue
        fields = [
            "id",
            "dying_unit",
            "dying_lot_number",
            "date",
            "dying_issue_lot",
        ]
        read_only_fields = ["id", "dying_lot_number"]


class DyingIssueLotsSerializer(serializers.ModelSerializer):
    class Serializer(serializers.ModelSerializer):
        class Meta:
            model = DyingIssueDetail
            fields = [
                "quantity",
                "actual_gazaana",
                "expected_gazaana",
                "warehouse",
            ]

    detail = Serializer(many=True, required=True)

    class Meta:
        model = DyingIssueLot
        fields = ["id", "raw_lot_number", "dying_issue"]
        read_only_fields = ["id", "dying_issue"]


class IssueForDyingSerializer(UniqueLotNumbers, serializers.ModelSerializer):
    lots = DyingIssueLotsSerializer(many=True, required=True)

    class Meta:
        model = DyingIssue
        fields = [
            "id",
            "dying_unit",
            "manual_serial",
            "date",
            "lots",
        ]
        read_only_fields = ["id", "dying_lot_number"]

    def create(self, validated_data):
        request = self.context["request"]
        DyingIssue.create_dying_issue(
            {**validated_data}, user=request.user, branch=request.branch
        )
        validated, error = validate_raw_inventory(request.branch)
        if not validated:
            raise ValidationError(error)
        return validated_data
