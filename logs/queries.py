from .models import Log


class LogQuery:
    def get_queryset(self):
        return Log.objects.filter(branch=self.request.branch)
