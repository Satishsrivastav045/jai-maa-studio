import json

from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .models import Booking, Testimonial, UnknownQuestion


@override_settings(SECURE_SSL_REDIRECT=False)
class PublicApiTests(TestCase):
    def test_booking_requires_valid_phone(self):
        response = self.client.post(
            "/save-booking/",
            {
                "name": "Amit",
                "phone": "abcd",
                "event": "Wedding",
                "event_date": "2026-12-01",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Booking.objects.count(), 0)

    def test_booking_can_be_saved(self):
        response = self.client.post(
            "/save-booking/",
            {
                "name": "Amit",
                "phone": "9936759702",
                "event": "Wedding",
                "event_date": "2026-12-01",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Booking.objects.count(), 1)

    def test_feedback_is_saved_pending_approval(self):
        response = self.client.post(
            "/feedback/",
            data=json.dumps({"name": "Priya", "message": "Great work", "rating": 8}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        testimonial = Testimonial.objects.get()
        self.assertFalse(testimonial.approved)
        self.assertEqual(testimonial.rating, 5)

    def test_chatbot_records_unknown_question(self):
        response = self.client.post(
            "/chatbot/",
            data=json.dumps({"message": "Can you recommend wardrobe colors?"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(UnknownQuestion.objects.count(), 1)


@override_settings(SECURE_SSL_REDIRECT=False)
class SecurityTests(TestCase):
    def test_dashboard_requires_login(self):
        response = self.client.get("/dashboard/")

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("admin:login"), response["Location"])

    def test_post_apis_require_csrf_when_checks_are_enabled(self):
        client = Client(enforce_csrf_checks=True)

        response = client.post(
            "/feedback/",
            data=json.dumps({"name": "Priya", "message": "Great work"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)
