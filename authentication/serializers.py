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
            user_branch = UserBranchRelation.objects.get(
                user=self.context["request"].user, branch=validated_data["branch_id"]
            )
        except UserBranchRelation.DoesNotExist:
            raise PermissionDenied("You are not a member of this branch")

        user_branch.login()

        # log out from other branches
        other_branches = UserBranchRelation.objects.filter(
            user=self.context["request"].user
        ).exclude(branch=user_branch.branch)

        for branch in other_branches:
            branch.is_logged_in = False
            branch.save()

        return validated_data
