from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views import View

from .models import Report


class ReportListView(LoginRequiredMixin, View):
    def get(self, request):
        reports = list(Report.objects.values("id", "title", "report_type", "created_at", "updated_at"))
        return JsonResponse({"reports": reports})
