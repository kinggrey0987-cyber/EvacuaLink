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
        self.admin_viewer = User.objects.create_user(
            username="admin_viewer",
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

    def test_admin_viewer_cannot_create_evacuation_center(self):
        self.client.force_login(self.admin_viewer)

        response = self.client.get(reverse("evacuation-center-add"))

        self.assertEqual(response.status_code, 403)

    def test_staff_can_create_evacuation_center(self):
        self.client.force_login(self.staff)

        response = self.client.get(reverse("evacuation-center-add"))

        self.assertEqual(response.status_code, 200)

    def test_admin_viewer_cannot_delete_evacuation_center(self):
        self.client.force_login(self.admin_viewer)

        response = self.client.get(reverse("evacuation-center-delete", args=[self.center.pk]))

        self.assertEqual(response.status_code, 403)

    def test_staff_can_delete_evacuation_center(self):
        self.client.force_login(self.staff)

        response = self.client.get(reverse("evacuation-center-delete", args=[self.center.pk]))

        self.assertEqual(response.status_code, 200)

    def test_admin_viewer_detail_view_hides_edit_button_and_shows_map(self):
        self.client.force_login(self.admin_viewer)

        response = self.client.get(reverse("evacuation-center-detail", args=[self.center.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="centerLocationMap"')
        self.assertNotContains(response, reverse("evacuation-center-edit", args=[self.center.pk]))

    def test_staff_detail_view_shows_edit_button(self):
        self.client.force_login(self.staff)

        response = self.client.get(reverse("evacuation-center-detail", args=[self.center.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("evacuation-center-edit", args=[self.center.pk]))
