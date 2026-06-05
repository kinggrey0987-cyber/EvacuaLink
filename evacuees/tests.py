from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from evacuation_centers.models import EvacuationCenter
from evacuees.models import Evacuee, TransferRecord
from families.models import Family


User = get_user_model()


class EvacueeAssignmentTransferTests(TestCase):
    def setUp(self):
        self.responder = User.objects.create_user(
            username="responder",
            password="StrongerPass123!",
            role=User.Role.VOLUNTEER,
        )
        self.staff = User.objects.create_user(
            username="staff",
            password="StrongerPass123!",
            role=User.Role.STAFF,
        )
        self.family = Family.objects.create(
            family_code="FAM-001",
            family_name="Dela Cruz",
            contact_person="Juan Dela Cruz",
        )
        self.origin = EvacuationCenter.objects.create(
            name="Origin Center",
            address="Origin Address",
            latitude=10.900000,
            longitude=123.000000,
            capacity=2,
            current_occupancy=0,
            status=EvacuationCenter.Status.OPEN,
        )
        self.destination = EvacuationCenter.objects.create(
            name="Destination Center",
            address="Destination Address",
            latitude=10.910000,
            longitude=123.010000,
            capacity=1,
            current_occupancy=0,
            status=EvacuationCenter.Status.OPEN,
        )
        self.full_center = EvacuationCenter.objects.create(
            name="Full Center",
            address="Full Address",
            latitude=10.920000,
            longitude=123.020000,
            capacity=1,
            current_occupancy=1,
            status=EvacuationCenter.Status.FULL,
        )
        self.evacuee = Evacuee.objects.create(
            first_name="Maria",
            last_name="Dela Cruz",
            age=35,
            gender=Evacuee.Gender.FEMALE,
            family=self.family,
            status=Evacuee.Status.REGISTERED,
        )
        self.client.force_login(self.responder)

    def test_assignment_updates_evacuee_and_center_occupancy(self):
        response = self.client.post(
            reverse("evacuee-assign", args=[self.evacuee.pk]),
            {"evacuation_center": self.origin.pk},
        )

        self.assertRedirects(response, reverse("evacuee-list"), fetch_redirect_response=False)
        self.evacuee.refresh_from_db()
        self.origin.refresh_from_db()
        self.assertEqual(self.evacuee.evacuation_center, self.origin)
        self.assertEqual(self.evacuee.status, Evacuee.Status.CHECKED_IN)
        self.assertEqual(self.origin.current_occupancy, 1)
        self.assertEqual(self.origin.status, EvacuationCenter.Status.OPEN)

    def test_assignment_rejects_full_center(self):
        response = self.client.post(
            reverse("evacuee-assign", args=[self.evacuee.pk]),
            {"evacuation_center": self.full_center.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.evacuee.refresh_from_db()
        self.full_center.refresh_from_db()
        self.assertIsNone(self.evacuee.evacuation_center)
        self.assertEqual(self.full_center.current_occupancy, 1)

    def test_transfer_updates_old_and_new_center_occupancy(self):
        self.evacuee.evacuation_center = self.origin
        self.evacuee.status = Evacuee.Status.CHECKED_IN
        self.evacuee.save()
        self.origin.current_occupancy = 1
        self.origin.save()

        response = self.client.post(
            reverse("evacuee-transfer", args=[self.evacuee.pk]),
            {
                "from_center": self.origin.pk,
                "to_center": self.destination.pk,
                "transfer_date": timezone.now().strftime("%Y-%m-%dT%H:%M"),
                "reason": "Move closer to relatives",
            },
        )

        self.assertRedirects(response, reverse("evacuee-list"), fetch_redirect_response=False)
        self.evacuee.refresh_from_db()
        self.origin.refresh_from_db()
        self.destination.refresh_from_db()
        self.assertEqual(self.evacuee.evacuation_center, self.destination)
        self.assertEqual(self.evacuee.status, Evacuee.Status.TRANSFERRED)
        self.assertEqual(self.origin.current_occupancy, 0)
        self.assertEqual(self.destination.current_occupancy, 1)
        self.assertEqual(self.destination.status, EvacuationCenter.Status.FULL)
        self.assertTrue(TransferRecord.objects.filter(evacuee=self.evacuee, from_center=self.origin, to_center=self.destination).exists())

    def test_transfer_rejects_full_destination(self):
        self.evacuee.evacuation_center = self.origin
        self.evacuee.status = Evacuee.Status.CHECKED_IN
        self.evacuee.save()
        self.origin.current_occupancy = 1
        self.origin.save()

        response = self.client.post(
            reverse("evacuee-transfer", args=[self.evacuee.pk]),
            {
                "from_center": self.origin.pk,
                "to_center": self.full_center.pk,
                "transfer_date": timezone.now().strftime("%Y-%m-%dT%H:%M"),
                "reason": "Attempt invalid transfer",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.evacuee.refresh_from_db()
        self.origin.refresh_from_db()
        self.full_center.refresh_from_db()
        self.assertEqual(self.evacuee.evacuation_center, self.origin)
        self.assertEqual(self.origin.current_occupancy, 1)
        self.assertEqual(self.full_center.current_occupancy, 1)
        self.assertFalse(TransferRecord.objects.filter(evacuee=self.evacuee, to_center=self.full_center).exists())

    def test_staff_detail_view_hides_edit_button_and_shows_assigned_center_map(self):
        self.evacuee.evacuation_center = self.origin
        self.evacuee.status = Evacuee.Status.CHECKED_IN
        self.evacuee.save()
        self.client.force_login(self.staff)

        response = self.client.get(reverse("evacuee-detail", args=[self.evacuee.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="evacueeCenterMap"')
        self.assertContains(response, self.origin.name)
        self.assertNotContains(response, reverse("evacuee-edit", args=[self.evacuee.pk]))

    def test_detail_view_shows_unassigned_message_without_center(self):
        self.client.force_login(self.staff)

        response = self.client.get(reverse("evacuee-detail", args=[self.evacuee.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "not assigned to an evacuation center")
        self.assertNotContains(response, 'id="evacueeCenterMap"')
