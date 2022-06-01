from .models import DyingIssue, DyingUnit


class DyingUnitQuery:
    def get_queryset(self):
        return DyingUnit.objects.filter(branch=self.request.branch)


class DyingIssueQuery:
    def get_queryset(self):
        return DyingIssue.objects.filter(
            dying_unit__branch=self.request.branch
        ).prefetch_related("dying_issue_lot")
