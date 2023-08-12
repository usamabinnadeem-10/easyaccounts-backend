from django.contrib.auth.models import User
from rest_framework import serializers, status
from rest_framework.exceptions import PermissionDenied

from .models import UserBranchRelation
from .utils import validate_if_permissions_exist


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
    permissions = serializers.ListField(read_only=True)

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
        validated_data["permissions"] = user_branch.permissions
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
    username = serializers.CharField(source="user.username")

    class Meta:
        model = UserBranchRelation
        fields = ["id", "username", "role", "permissions", "is_active", "is_logged_in"]
        read_only_fields = [
            "id",
            "username",
            "role",
            "permissions",
            "is_active",
            "is_logged_in",
        ]
        depth = 1


class EditUserPermissionsForBranchSerializer(serializers.ModelSerializer):
    new_permissions = serializers.ListField(write_only=True)
    # new_is_active = serializers.BooleanField(write_only=True)

    class Meta:
        model = UserBranchRelation
        fields = [
            "id",
            "role",
            "permissions",
            "new_permissions",
            "is_active",
            # "new_is_active",
            "is_logged_in",
        ]
        read_only_fields = [
            "id",
            "role",
            "permissions",
            "is_active",
            "is_logged_in",
        ]
        depth = 1

    def validate(self, data):
        if validate_if_permissions_exist(data["new_permissions"]):
            return data
        raise serializers.ValidationError(
            "No such permissions exist", status.HTTP_400_BAD_REQUEST
        )

    def update(self, instance, validated_data):
        instance.permissions = validated_data["new_permissions"]
        instance.save()
        return instance
