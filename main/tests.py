import json

from django.contrib.auth.models import User
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
        self.assertEqual(Booking.objects.get().status, Booking.STATUS_NEW)
        self.assertIn("whatsapp_url", response.json())

    def test_availability_reports_existing_active_booking(self):
        Booking.objects.create(
            name="Amit",
            phone="9936759702",
            event="Wedding",
            event_date="2026-12-01",
            status=Booking.STATUS_CONFIRMED,
        )

        response = self.client.get("/check-availability/?event_date=2026-12-01")

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["available"])

    def test_availability_ignores_cancelled_booking(self):
        Booking.objects.create(
            name="Amit",
            phone="9936759702",
            event="Wedding",
            event_date="2026-12-01",
            status=Booking.STATUS_CANCELLED,
        )

        response = self.client.get("/check-availability/?event_date=2026-12-01")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["available"])

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

    def test_logged_in_admin_can_update_booking_status(self):
        User.objects.create_user(username="admin", password="pass12345", is_staff=True)
        self.client.login(username="admin", password="pass12345")
        booking = Booking.objects.create(
            name="Amit",
            phone="9936759702",
            event="Wedding",
            event_date="2026-12-01",
        )

        response = self.client.post(
            f"/dashboard/bookings/{booking.id}/status/",
            {"status": Booking.STATUS_CONFIRMED},
        )

        self.assertEqual(response.status_code, 200)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.STATUS_CONFIRMED)


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
