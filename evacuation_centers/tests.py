from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from evacuation_centers.models import EvacuationCenter


User = get_user_model()


class EvacuationCenterPermissionTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username="staff",
            password="StrongerPass123!",
            role=User.Role.STAFF,
        )
        self.volunteer = User.objects.create_user(
            username="volunteer",
            password="StrongerPass123!",
            role=User.Role.VOLUNTEER,
        )
        self.admin = User.objects.create_user(
            username="admin",
            password="StrongerPass123!",
            role=User.Role.ADMIN,
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

    def test_staff_cannot_create_evacuation_center(self):
        self.client.force_login(self.staff)

        response = self.client.get(reverse("evacuation-center-add"))

        self.assertEqual(response.status_code, 403)

    def test_emergency_responder_can_create_evacuation_center(self):
        self.client.force_login(self.volunteer)

        response = self.client.get(reverse("evacuation-center-add"))

        self.assertEqual(response.status_code, 200)

    def test_non_admin_cannot_delete_evacuation_center(self):
        self.client.force_login(self.volunteer)

        response = self.client.get(reverse("evacuation-center-delete", args=[self.center.pk]))

        self.assertEqual(response.status_code, 403)

    def test_operational_admin_can_delete_evacuation_center(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("evacuation-center-delete", args=[self.center.pk]))

        self.assertEqual(response.status_code, 200)
