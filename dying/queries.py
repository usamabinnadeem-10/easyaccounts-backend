from .models import DyingUnit


class DyingUnitQuery:
    def get_queryset(self):
        return DyingUnit.objects.filter(branch=self.request.branch)
