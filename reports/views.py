"""
Views for report generation, viewing, and PDF export.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, FileResponse
from django.shortcuts import render
from django.views import View
from django.views.generic import TemplateView
from django.utils import timezone
from io import BytesIO

from .forms import ReportFilterForm
from .utils import (
    generate_occupancy_report,
    generate_family_reunification_report,
    generate_special_needs_report,
    generate_incident_report,
)

try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False


class ReportDashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard for report selection and generation"""

    template_name = "reports/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = ReportFilterForm()
        context["weasyprint_available"] = WEASYPRINT_AVAILABLE
        return context


class ReportGeneratorView(LoginRequiredMixin, View):
    """Generate and display reports with optional PDF export"""

    template_map = {
        "OCCUPANCY": "reports/occupancy_report.html",
        "FAMILY_REUNIFICATION": "reports/family_reunification_report.html",
        "SPECIAL_NEEDS": "reports/special_needs_report.html",
        "INCIDENT": "reports/incident_report.html",
    }

    def post(self, request):
        form = ReportFilterForm(request.POST)

        if form.is_valid():
            report_type = form.cleaned_data.get("report_type")
            date_from = form.cleaned_data.get("date_from")
            date_to = form.cleaned_data.get("date_to")
            evacuation_center = form.cleaned_data.get("evacuation_center")
            export_format = form.cleaned_data.get("format")

            # Generate appropriate report
            if report_type == "OCCUPANCY":
                report_data = generate_occupancy_report(date_from, date_to, evacuation_center)
            elif report_type == "FAMILY_REUNIFICATION":
                report_data = generate_family_reunification_report(date_from, date_to, evacuation_center)
            elif report_type == "SPECIAL_NEEDS":
                report_data = generate_special_needs_report(date_from, date_to, evacuation_center)
            elif report_type == "INCIDENT":
                report_data = generate_incident_report(date_from, date_to, evacuation_center)
            else:
                return render(request, "reports/dashboard.html", {
                    "form": form,
                    "error": "Invalid report type selected.",
                    "weasyprint_available": WEASYPRINT_AVAILABLE,
                })

            # Add user and timestamp
            report_data["generated_by"] = request.user.get_full_name() or request.user.username
            report_data["user_role"] = request.user.get_role_display()

            # Export as PDF if requested
            if export_format == "pdf":
                if not WEASYPRINT_AVAILABLE:
                    return render(request, "reports/dashboard.html", {
                        "form": form,
                        "error": "PDF export is not available. Please try HTML format.",
                        "weasyprint_available": WEASYPRINT_AVAILABLE,
                    })
                return self.export_pdf(report_type, report_data)

            # Display as HTML
            template = self.template_map.get(report_type, "reports/dashboard.html")
            return render(request, template, {
                "report_data": report_data,
                "form": form,
            })

        # Form invalid
        return render(request, "reports/dashboard.html", {
            "form": form,
            "weasyprint_available": WEASYPRINT_AVAILABLE,
        })

    def export_pdf(self, report_type, report_data):
        """Generate and return PDF file"""
        template = self.template_map.get(report_type)

        # Render template to HTML string
        from django.template.loader import render_to_string
        html_string = render_to_string(template, {"report_data": report_data, "pdf_export": True})

        # Convert HTML to PDF
        try:
            pdf_file = BytesIO()
            HTML(string=html_string).write_pdf(pdf_file)
            pdf_file.seek(0)

            filename = f"{report_type.lower()}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            response = HttpResponse(pdf_file.getvalue(), content_type="application/pdf")
            response["Content-Disposition"] = f"attachment; filename={filename}"
            return response
        except Exception as e:
            return HttpResponse(f"Error generating PDF: {str(e)}", status=500)


class ReportListView(LoginRequiredMixin, TemplateView):
    """List all generated reports"""

    template_name = "reports/report_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .models import Report
        context["reports"] = Report.objects.all().select_related("prepared_by", "evacuation_center")
        return context

