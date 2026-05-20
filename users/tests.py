from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


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
