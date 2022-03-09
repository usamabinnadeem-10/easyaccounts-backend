from django.db.models import Manager


class UserBranchManager(Manager):
    def logout_all(self, user):
        user_branches = self.filter(user=user)

        for branch in user_branches:
            branch.is_logged_in = False
            branch.save()

    def logout_from_other_branches(self, user, branch):
        other_branches = self.filter(user=user).exclude(branch=branch)

        for branch in other_branches:
            branch.is_logged_in = False
            branch.save()
