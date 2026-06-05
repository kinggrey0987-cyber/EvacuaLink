from django.contrib.auth import get_user_model
from django.test import TestCase

from emergency.models import EmergencyIncident
from evacuation_centers.models import EvacuationCenter
from reports.utils import generate_incident_report, generate_occupancy_report


User = get_user_model()


class ReportGenerationTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username="staff_report",
            password="StrongerPass123!",
            role=User.Role.STAFF,
        )
        self.center = EvacuationCenter.objects.create(
            name="Alicante Elementary School",
            address="Alicante",
            latitude=10.900000,
            longitude=123.000000,
            capacity=10,
            current_occupancy=3,
            status=EvacuationCenter.Status.OPEN,
        )
        EmergencyIncident.objects.create(
            title="Water Supply Interrupted",
            description="Main water line damaged",
            location="Barangay Hall",
            severity=EmergencyIncident.Severity.HIGH,
            status=EmergencyIncident.Status.OPEN,
            reported_by=self.staff,
            evacuation_center=self.center,
        )

    def test_occupancy_report_uses_existing_center_fields(self):
        report = generate_occupancy_report(evacuation_center=self.center)

        self.assertEqual(report["centers"][0]["location"], self.center.address)
        self.assertEqual(report["centers"][0]["occupancy"], 3)

    def test_incident_report_uses_existing_incident_fields(self):
        report = generate_incident_report(evacuation_center=self.center)

        self.assertEqual(report["summary"]["total_incidents"], 1)
        self.assertEqual(report["incidents"][0]["evacuation_center"], self.center.name)
