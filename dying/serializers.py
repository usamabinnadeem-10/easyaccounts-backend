from rawtransactions.models import RawPurchaseLotDetail
from rawtransactions.serializers import StockCheck, UniqueLotNumbers
from rest_framework import serializers

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
            return RawPurchaseLotDetail.objects.filter(
                lot_number=obj.lot_number.id
            ).values()
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


class LotNumberAndDetail(serializers.ModelSerializer):
    class Serializer(serializers.ModelSerializer):
        class Meta:
            model = DyingIssueDetail
            fields = [
                "quantity",
                "actual_gazaana",
                "expected_gazaana",
                "formula",
                "warehouse",
            ]

    detail = Serializer(many=True, required=True)

    class Meta:
        model = DyingIssueLot
        fields = ["id", "lot_number", "dying_lot", "detail"]
        read_only_fields = ["id", "dying_lot"]


class IssueForDyingSerializer(UniqueLotNumbers, StockCheck, serializers.ModelSerializer):

    data = LotNumberAndDetail(many=True, required=True)

    class Meta:
        model = DyingIssue
        fields = [
            "id",
            "dying_unit",
            "dying_lot_number",
            "date",
            "data",
        ]
        read_only_fields = ["id", "dying_lot_number"]

    def create(self, validated_data):
        self.check_stock(validated_data["data"])
        data = validated_data.pop("data")
        user = self.context["request"].user
        dying_issue_instance = DyingIssue.objects.create(
            **validated_data,
            user=user,
            dying_lot_number=DyingIssue.get_next_serial(
                "dying_lot_number", branch=self.branch
            )
        )
        for lot in data:
            dying_issue_lot_instance = DyingIssueLot.objects.create(
                dying_lot=dying_issue_instance,
                lot_number=lot["lot_number"],
            )
            current_details = []
            for detail in lot["detail"]:
                current_details.append(
                    DyingIssueDetail(dying_lot_number=dying_issue_lot_instance, **detail)
                )
            DyingIssueDetail.objects.bulk_create(current_details)
        validated_data["data"] = data
        return validated_data
