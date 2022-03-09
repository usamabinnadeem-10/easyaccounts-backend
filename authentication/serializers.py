from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from .models import UserBranchRelation


class UserBranchSerializer(serializers.ModelSerializer):

    branch_name = serializers.CharField(source="branch.name")
    branch_id = serializers.UUIDField(source="branch.id")

    class Meta:
        model = UserBranchRelation
        fields = ["branch_name", "branch_id"]


class LoginSerializer(serializers.Serializer):

    branch_id = serializers.UUIDField()

    def create(self, validated_data):

        try:
            user = self.context["request"].user
            branch = validated_data["branch_id"]
            user_branch = UserBranchRelation.objects.filter(user=user, branch=branch)
            print(user_branch)
            user_branch = UserBranchRelation.objects.get(user=user, branch=branch)
        except UserBranchRelation.DoesNotExist:
            raise PermissionDenied("You are not a member of this branch")

        user_branch.login()
        UserBranchRelation.utils.logout_from_other_branches(user, branch)

        return validated_data


class LogoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserBranchRelation
        fields = ["id"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        UserBranchRelation.utils.logout_all(self.context["request"].user)

        return {}
