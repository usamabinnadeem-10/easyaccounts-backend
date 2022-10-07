from django.contrib.auth.models import User
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
    branch_name = serializers.CharField(read_only=True)
    role = serializers.CharField(read_only=True)

    def create(self, validated_data):

        try:
            user = self.context["request"].user
            branch = validated_data["branch_id"]
            user_branch = UserBranchRelation.objects.filter(user=user, branch=branch)
            user_branch = UserBranchRelation.objects.get(user=user, branch=branch)
        except UserBranchRelation.DoesNotExist:
            raise PermissionDenied("You are not a member of this branch")

        user_branch.login()
        UserBranchRelation.utils.logout_from_other_branches(user, branch)

        validated_data["branch_name"] = user_branch.branch.name
        validated_data["role"] = user_branch.role
        return validated_data


class LogoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserBranchRelation
        fields = ["id"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        UserBranchRelation.utils.logout_all(self.context["request"].user)

        return {}


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name"]
        read_only_fields = ["id", "username", "first_name", "last_name"]
