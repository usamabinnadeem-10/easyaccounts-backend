from .models import Asset


class AssetQuery:
    def get_queryset(self):
        return Asset.objects.filter(branch=self.request.branch)
