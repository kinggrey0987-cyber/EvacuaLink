from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from emergency.models import EmergencyHelpRequest


User = get_user_model()


class HelpRequestAccessTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username="staff_help",
            password="StrongerPass123!",
            role=User.Role.STAFF,
        )
        self.admin = User.objects.create_user(
            username="admin_help",
            password="StrongerPass123!",
            role=User.Role.ADMIN,
        )
        self.help_request = EmergencyHelpRequest.objects.create(
            requester_name="Citizen One",
            contact_number="555-1234",
            location_description="Near barangay hall",
            message="Need assistance",
            latitude=10.900000,
            longitude=123.000000,
        )

    def test_help_request_json_requires_login(self):
        response = self.client.get(reverse("emergency-api-help-requests"))

        self.assertEqual(response.status_code, 302)

    def test_staff_can_access_help_request_json(self):
        self.client.force_login(self.staff)

        response = self.client.get(reverse("emergency-api-help-requests"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["help_requests"][0]["requester_name"], "Citizen One")

    def test_admin_can_view_help_request_list(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("help-request-list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.help_request.requester_name)
