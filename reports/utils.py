"""
Utilities for report generation and PDF export.
"""

from django.utils import timezone
from datetime import datetime

from evacuees.models import Evacuee
from families.models import Family
from evacuation_centers.models import EvacuationCenter
from emergency.models import EmergencyIncident, EmergencyHelpRequest


def generate_occupancy_report(date_from=None, date_to=None, evacuation_center=None):
    """Generate occupancy report data for evacuation centers"""

    centers = EvacuationCenter.objects.all()
    if evacuation_center:
        centers = centers.filter(pk=evacuation_center.pk)

    centers = centers.prefetch_related("evacuees")

    center_data = []
    total_capacity = 0
    total_occupancy = 0

    for center in centers:
        occupancy = center.current_occupancy
        capacity = center.capacity
        available = center.available_space()
        occupancy_percentage = int((occupancy / capacity) * 100) if capacity > 0 else 0

        center_data.append({
            "name": center.name,
            "location": center.address,
            "address": center.address,
            "capacity": capacity,
            "occupancy": occupancy,
            "available": available,
            "occupancy_percentage": occupancy_percentage,
            "status": center.get_status_display(),
            "contact": "",
        })

        total_capacity += capacity
        total_occupancy += occupancy

    total_occupancy_percentage = int((total_occupancy / total_capacity) * 100) if total_capacity > 0 else 0

    return {
        "report_type": "Occupancy Report",
        "generated_at": timezone.now(),
        "date_from": date_from or "All time",
        "date_to": date_to or "All time",
        "centers": center_data,
        "summary": {
            "total_centers": len(center_data),
            "total_capacity": total_capacity,
            "total_occupancy": total_occupancy,
            "total_available": total_capacity - total_occupancy,
            "occupancy_percentage": total_occupancy_percentage,
            "open_centers": sum(1 for c in center_data if c["status"] == "Open"),
            "full_centers": sum(1 for c in center_data if c["status"] == "Full"),
            "closed_centers": sum(1 for c in center_data if c["status"] == "Closed"),
        },
    }


def generate_family_reunification_report(date_from=None, date_to=None, evacuation_center=None):
    """Generate family reunification status report"""

    families = Family.objects.all().prefetch_related("evacuees")
    if evacuation_center:
        families = families.filter(evacuees__evacuation_center=evacuation_center).distinct()

    family_data = []

    for family in families:
        total_members = family.member_count
        reunited_members = family.reunited_count
        missing_members = family.missing_count
        checked_in_members = family.checked_in_count

        reunification_percentage = int((reunited_members / total_members) * 100) if total_members > 0 else 0

        family_data.append({
            "code": family.family_code,
            "name": family.family_name,
            "contact_person": family.contact_person.full_name if family.contact_person else "None",
            "contact_number": family.contact_number,
            "total_members": total_members,
            "reunited_members": reunited_members,
            "missing_members": missing_members,
            "checked_in_members": checked_in_members,
            "reunification_percentage": reunification_percentage,
            "status": family.get_reunification_status_display(),
        })

    # Calculate summary statistics
    total_families = len(family_data)
    pending_families = sum(1 for f in family_data if f["status"] == "Pending")
    partial_families = sum(1 for f in family_data if f["status"] == "Partially Reunified")
    reunified_families = sum(1 for f in family_data if f["status"] == "Reunified")
    unknown_families = sum(1 for f in family_data if f["status"] == "Unknown")

    total_members = sum(f["total_members"] for f in family_data)
    total_reunited = sum(f["reunited_members"] for f in family_data)
    total_missing = sum(f["missing_members"] for f in family_data)

    overall_reunification = int((total_reunited / total_members) * 100) if total_members > 0 else 0

    return {
        "report_type": "Family Reunification Report",
        "generated_at": timezone.now(),
        "date_from": date_from or "All time",
        "date_to": date_to or "All time",
        "families": family_data,
        "summary": {
            "total_families": total_families,
            "pending_families": pending_families,
            "partial_families": partial_families,
            "reunified_families": reunified_families,
            "unknown_families": unknown_families,
            "total_members": total_members,
            "total_reunited": total_reunited,
            "total_missing": total_missing,
            "overall_reunification_percentage": overall_reunification,
        },
    }


def generate_special_needs_report(date_from=None, date_to=None, evacuation_center=None):
    """Generate special needs evacuees report"""

    evacuees = Evacuee.objects.filter(special_needs=True).select_related("family", "evacuation_center")

    if evacuation_center:
        evacuees = evacuees.filter(evacuation_center=evacuation_center)
    if date_from:
        evacuees = evacuees.filter(registered_at__date__gte=date_from)
    if date_to:
        evacuees = evacuees.filter(registered_at__date__lte=date_to)

    evacuee_data = []

    for evacuee in evacuees:
        evacuee_data.append({
            "full_name": evacuee.full_name,
            "age": evacuee.age,
            "gender": evacuee.get_gender_display(),
            "family_name": evacuee.family.family_name if evacuee.family else "Not assigned",
            "family_code": evacuee.family.family_code if evacuee.family else "N/A",
            "special_needs_description": evacuee.special_needs_description,
            "medical_condition": evacuee.medical_condition,
            "current_center": evacuee.evacuation_center.name if evacuee.evacuation_center else "Not assigned",
            "status": evacuee.get_status_display(),
            "registered_at": evacuee.registered_at,
        })

    return {
        "report_type": "Special Needs Report",
        "generated_at": timezone.now(),
        "date_from": date_from or "All time",
        "date_to": date_to or "All time",
        "evacuees": evacuee_data,
        "summary": {
            "total_special_needs": len(evacuee_data),
            "by_status": {
                "registered": sum(1 for e in evacuee_data if e["status"] == "Registered"),
                "checked_in": sum(1 for e in evacuee_data if e["status"] == "Checked In"),
                "reunited": sum(1 for e in evacuee_data if e["status"] == "Reunited"),
                "missing": sum(1 for e in evacuee_data if e["status"] == "Missing"),
            },
        },
    }


def generate_incident_report(date_from=None, date_to=None, evacuation_center=None):
    """Generate emergency incidents report"""

    incidents = EmergencyIncident.objects.all()

    if date_from:
        incidents = incidents.filter(reported_at__date__gte=date_from)
    if date_to:
        incidents = incidents.filter(reported_at__date__lte=date_to)
    if evacuation_center:
        incidents = incidents.filter(evacuation_center=evacuation_center)

    incidents = incidents.order_by("-reported_at")

    incident_data = []

    for incident in incidents:
        incident_data.append({
            "title": incident.title,
            "description": incident.description,
            "location": incident.location,
            "severity": incident.get_severity_display(),
            "status": incident.get_status_display(),
            "reported_at": incident.reported_at,
            "reported_by": incident.reported_by.get_full_name() if incident.reported_by else "Unknown",
            "evacuation_center": incident.evacuation_center.name if incident.evacuation_center else "Not linked",
            "resolved_at": incident.resolved_at,
        })

    # Summary statistics
    critical_incidents = sum(1 for i in incident_data if i["severity"] == "Critical")
    high_incidents = sum(1 for i in incident_data if i["severity"] == "High")
    open_incidents = sum(1 for i in incident_data if i["status"] == "Open")
    resolved_incidents = sum(1 for i in incident_data if i["status"] == "Resolved")

    return {
        "report_type": "Incident Report",
        "generated_at": timezone.now(),
        "date_from": date_from or "All time",
        "date_to": date_to or "All time",
        "incidents": incident_data,
        "summary": {
            "total_incidents": len(incident_data),
            "critical_incidents": critical_incidents,
            "high_incidents": high_incidents,
            "open_incidents": open_incidents,
            "resolved_incidents": resolved_incidents,
        },
    }


def generate_help_request_report(date_from=None, date_to=None):
    """Generate citizen SOS help requests report"""

    requests = EmergencyHelpRequest.objects.all()

    if date_from:
        requests = requests.filter(created_at__date__gte=date_from)
    if date_to:
        requests = requests.filter(created_at__date__lte=date_to)

    requests = requests.order_by("-created_at")

    request_data = []

    for req in requests:
        request_data.append({
            "requester_name": req.requester_name,
            "contact_number": req.contact_number,
            "location_description": req.location_description,
            "message": req.message,
            "priority": req.get_priority_display(),
            "status": req.get_status_display(),
            "created_at": req.created_at,
            "resolved_at": req.resolved_at,
        })

    # Summary statistics
    high_priority = sum(1 for r in request_data if r["priority"] == "High")
    pending_requests = sum(1 for r in request_data if r["status"] == "Pending")
    in_progress = sum(1 for r in request_data if r["status"] == "In Progress")
    resolved_requests = sum(1 for r in request_data if r["status"] == "Resolved")

    return {
        "report_type": "Help Request Report",
        "generated_at": timezone.now(),
        "date_from": date_from or "All time",
        "date_to": date_to or "All time",
        "requests": request_data,
        "summary": {
            "total_requests": len(request_data),
            "high_priority": high_priority,
            "pending_requests": pending_requests,
            "in_progress": in_progress,
            "resolved_requests": resolved_requests,
        },
    }
