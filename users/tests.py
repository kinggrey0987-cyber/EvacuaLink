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
        self.tech_admin = User.objects.create_user(
            username="techadmin",
            password="StrongerPass123!",
            role=User.Role.TECHNICAL_ADMIN,
        )
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

    def test_admin_dashboard_routes_to_overview_pages(self):
        self.client.force_login(self.admin)

        # Check dashboard redirects to admin-dashboard
        response = self.client.get(reverse("dashboard"))
        self.assertRedirects(response, reverse("admin-dashboard"), fetch_redirect_response=False)

        url_names = [
            "admin-dashboard",
            "family-list",
            "evacuee-list",
            "evacuation-center-list",
            "emergency-incident-list",
            "report-dashboard",
        ]

        for url_name in url_names:
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))
                self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse("emergency-incident-detail", args=[self.incident.pk]))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse("emergency-incident-edit", args=[self.incident.pk]))
        self.assertEqual(response.status_code, 403)

    def test_admin_dashboard_does_not_link_to_user_management(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("admin-dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, reverse("evacualink_admin:index"))
        self.assertNotContains(response, reverse("user_list"))

    def test_admin_dashboard_hides_staff_write_actions(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("admin-dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, reverse("family-register"))
        self.assertNotContains(response, reverse("evacuee-register"))
        self.assertNotContains(response, reverse("evacuation-center-add"))

    def test_staff_can_manage_operational_pages_but_not_users(self):
        self.client.force_login(self.staff)

        # Check dashboard redirects to staff-dashboard
        response = self.client.get(reverse("dashboard"))
        self.assertRedirects(response, reverse("staff-dashboard"), fetch_redirect_response=False)

        allowed_url_names = [
            "staff-dashboard",
            "family-list",
            "evacuee-list",
            "evacuation-center-list",
            "family-register",
            "evacuee-register",
            "evacuation-center-add",
            "emergency-incident-create",
        ]
        forbidden_url_names = [
            "user_list",
            "report-dashboard",
        ]

        for url_name in allowed_url_names:
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))
                self.assertEqual(response.status_code, 200)

        for url_name in forbidden_url_names:
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))
                self.assertEqual(response.status_code, 403)

    def test_technical_admin_can_manage_user_accounts(self):
        self.client.force_login(self.tech_admin)

        response = self.client.get(reverse("user_list"))

        self.assertEqual(response.status_code, 200)

    def test_test_data_command_refreshes_existing_accounts_with_three_roles(self):
        self.tech_admin.set_password("OldPass123!")
        self.tech_admin.save()

        call_command("create_test_data", verbosity=0)

        self.tech_admin.refresh_from_db()
        self.admin.refresh_from_db()
        self.staff.refresh_from_db()
        self.assertEqual(self.tech_admin.role, User.Role.TECHNICAL_ADMIN)
        self.assertTrue(self.tech_admin.is_staff)
        self.assertTrue(self.tech_admin.is_superuser)
        self.assertTrue(self.tech_admin.check_password("techadmin123"))
        self.assertEqual(self.admin.role, User.Role.ADMIN)
        self.assertEqual(self.staff.role, User.Role.STAFF)
