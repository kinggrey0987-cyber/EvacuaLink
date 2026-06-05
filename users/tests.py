from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from evacuation_centers.models import EvacuationCenter
from emergency.models import EmergencyIncident
from families.models import Family

User = get_user_model()


class AuthenticationViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="staff",
            password="StrongerPass123!",
            role=User.Role.STAFF,
            first_name="System",
            last_name="Staff",
            email="staff@example.com",
        )

    def test_login_rejects_external_next_redirect(self):
        response = self.client.post(
            f"{reverse('login')}?next=https://evil.example/phishing",
            {"username": "staff", "password": "StrongerPass123!"},
        )

        self.assertRedirects(response, reverse("dashboard"), fetch_redirect_response=False)

    def test_login_allows_local_next_redirect(self):
        response = self.client.post(
            f"{reverse('login')}?next={reverse('evacuee-list')}",
            {"username": "staff", "password": "StrongerPass123!"},
        )

        self.assertRedirects(response, reverse("evacuee-list"), fetch_redirect_response=False)

    def test_profile_renders_html_template(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("user-profile"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/profile.html")
        self.assertContains(response, "User Profile")
        self.assertEqual(response.headers["Content-Type"].split(";")[0], "text/html")


class OperationalDashboardRouteTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin",
            password="StrongerPass123!",
            role=User.Role.ADMIN,
        )
        self.staff = User.objects.create_user(
            username="staff_route",
            password="StrongerPass123!",
            role=User.Role.STAFF,
        )
        self.family = Family.objects.create(
            family_code="FAM-001",
            family_name="Dela Cruz",
            contact_person="Juan Dela Cruz",
        )
        self.center = EvacuationCenter.objects.create(
            name="Alicante Elementary School",
            address="Alicante",
            latitude=10.900000,
            longitude=123.000000,
            capacity=10,
            current_occupancy=0,
            status=EvacuationCenter.Status.OPEN,
        )
        self.incident = EmergencyIncident.objects.create(
            title="Structure Damage",
            description="Roof damage at evacuation center",
            location="Alicante Elementary School",
            severity=EmergencyIncident.Severity.HIGH,
            status=EmergencyIncident.Status.OPEN,
            reported_by=self.admin,
            evacuation_center=self.center,
        )

    def test_operational_admin_dashboard_routes_to_workflow_pages(self):
        self.client.force_login(self.admin)

        url_names = [
            "dashboard",
            "family-register",
            "evacuee-register",
            "evacuation-center-add",
            "emergency-incident-list",
            "emergency-incident-create",
            "report-dashboard",
            "user_list",
        ]

        for url_name in url_names:
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))
                self.assertEqual(response.status_code, 200)

        detail_url_names = [
            "emergency-incident-detail",
            "emergency-incident-edit",
        ]

        for url_name in detail_url_names:
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name, args=[self.incident.pk]))
                self.assertEqual(response.status_code, 200)

    def test_operational_admin_nav_does_not_link_to_technical_admin(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, reverse("evacualink_admin:index"))
        self.assertContains(response, reverse("user_list"))

    def test_staff_dashboard_hides_responder_only_actions(self):
        self.client.force_login(self.staff)

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, reverse("family-register"))
        self.assertNotContains(response, reverse("evacuee-register"))
        self.assertNotContains(response, reverse("evacuation-center-add"))

    def test_staff_can_view_lists_but_cannot_open_restricted_create_pages(self):
        self.client.force_login(self.staff)

        allowed_url_names = [
            "dashboard",
            "family-list",
            "evacuee-list",
            "evacuation-center-list",
            "report-dashboard",
        ]
        forbidden_url_names = [
            "family-register",
            "evacuee-register",
            "evacuation-center-add",
            "emergency-incident-create",
        ]

        for url_name in allowed_url_names:
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))
                self.assertEqual(response.status_code, 200)

        for url_name in forbidden_url_names:
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))
                self.assertEqual(response.status_code, 403)

    def test_test_data_command_refreshes_existing_admin_account_role(self):
        self.admin.role = User.Role.TECHNICAL_ADMIN
        self.admin.set_password("OldPass123!")
        self.admin.save()

        call_command("create_test_data", verbosity=0)

        self.admin.refresh_from_db()
        self.assertEqual(self.admin.role, User.Role.ADMIN)
        self.assertFalse(self.admin.is_staff)
        self.assertFalse(self.admin.is_superuser)
        self.assertTrue(self.admin.check_password("admin123"))
