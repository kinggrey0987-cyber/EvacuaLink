"""
Views for report generation, viewing, and PDF export.
"""

import json
from io import BytesIO
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.dateparse import parse_datetime, parse_date
from django.views import View
from django.views.generic import TemplateView, DeleteView

from .forms import ReportFilterForm
from .models import Report
from .utils import (
    generate_occupancy_report,
    generate_family_reunification_report,
    generate_special_needs_report,
    generate_incident_report,
)

try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False


def deserialize_report_content(content_str):
    """Helper to deserialize report data and reconstruct datetime/date objects"""
    data = json.loads(content_str)
    
    # Parse generated_at
    if "generated_at" in data and isinstance(data["generated_at"], str):
        dt = parse_datetime(data["generated_at"])
        if dt:
            data["generated_at"] = dt
            
    # Parse date_from and date_to
    for key in ["date_from", "date_to"]:
        if key in data and isinstance(data[key], str) and data[key] != "All time":
            d = parse_date(data[key])
            if d:
                data[key] = d
                
    # Parse registered_at inside evacuees (Special Needs Report)
    if "evacuees" in data:
        for evacuee in data["evacuees"]:
            if "registered_at" in evacuee and isinstance(evacuee["registered_at"], str):
                dt = parse_datetime(evacuee["registered_at"])
                if dt:
                    evacuee["registered_at"] = dt
                    
    # Parse reported_at inside incidents (Incident Report)
    if "incidents" in data:
        for incident in data["incidents"]:
            if "reported_at" in incident and isinstance(incident["reported_at"], str):
                dt = parse_datetime(incident["reported_at"])
                if dt:
                    incident["reported_at"] = dt
                    
    return data


def export_report_pdf(report_type, report_data):
    """Helper to convert report HTML to PDF response"""
    template_map = {
        "OCCUPANCY": "reports/occupancy_report.html",
        "FAMILY_REUNIFICATION": "reports/family_reunification_report.html",
        "SPECIAL_NEEDS": "reports/special_needs_report.html",
        "INCIDENT": "reports/incident_report.html",
    }
    template = template_map.get(report_type)
    if not template:
        return HttpResponse("Invalid report type", status=400)

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


class ReportDashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard for report selection and generation"""

    template_name = "reports/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = ReportFilterForm()
        context["weasyprint_available"] = WEASYPRINT_AVAILABLE
        return context


class ReportGeneratorView(LoginRequiredMixin, View):
    """Generate, save, and display reports with optional PDF export"""

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

            # Save report to database
            center_name = evacuation_center.name if evacuation_center else "All Centers"
            report_type_display = dict(Report.ReportType.choices).get(report_type, report_type)
            timestamp = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
            title = f"{report_type_display} - {center_name} ({timestamp})"

            report = Report.objects.create(
                title=title[:150],
                report_type=report_type,
                evacuation_center=evacuation_center,
                content=json.dumps(report_data, cls=DjangoJSONEncoder),
                prepared_by=request.user
            )

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
                "report": report,
            })

        # Form invalid
        return render(request, "reports/dashboard.html", {
            "form": form,
            "weasyprint_available": WEASYPRINT_AVAILABLE,
        })

    def export_pdf(self, report_type, report_data):
        """Generate and return PDF file"""
        return export_report_pdf(report_type, report_data)


class ReportListView(LoginRequiredMixin, TemplateView):
    """List all generated reports"""

    template_name = "reports/report_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["reports"] = Report.objects.all().select_related("prepared_by", "evacuation_center")
        return context


class ReportDetailView(LoginRequiredMixin, View):
    """View details of a saved report with optional PDF export"""

    template_map = {
        "OCCUPANCY": "reports/occupancy_report.html",
        "FAMILY_REUNIFICATION": "reports/family_reunification_report.html",
        "SPECIAL_NEEDS": "reports/special_needs_report.html",
        "INCIDENT": "reports/incident_report.html",
    }

    def get(self, request, pk):
        report = get_object_or_404(Report, pk=pk)
        report_data = deserialize_report_content(report.content)

        export_format = request.GET.get("format")
        if export_format == "pdf":
            if not WEASYPRINT_AVAILABLE:
                template = self.template_map.get(report.report_type, "reports/dashboard.html")
                return render(request, template, {
                    "report_data": report_data,
                    "report": report,
                    "error": "PDF export is not available. Please view in browser.",
                })
            return export_report_pdf(report.report_type, report_data)

        template = self.template_map.get(report.report_type, "reports/dashboard.html")
        return render(request, template, {
            "report_data": report_data,
            "report": report,
        })


class ReportDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a generated report"""
    model = Report
    template_name = "reports/report_confirm_delete.html"
    success_url = reverse_lazy("report-list")


