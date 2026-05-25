import json

from django.core import mail
from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .models import Booking, ChatData, LeadClick, Package, Testimonial, UnknownQuestion


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
                "lead_source": "Instagram",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Booking.objects.count(), 1)
        booking = Booking.objects.get()
        self.assertEqual(booking.status, Booking.STATUS_NEW)
        self.assertEqual(str(booking.event_date_value), "2026-12-01")
        self.assertEqual(booking.lead_source, "Instagram")
        self.assertIn("whatsapp_url", response.json())

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        BOOKING_NOTIFICATION_EMAIL="owner@example.com",
        DEFAULT_FROM_EMAIL="site@example.com",
    )
    def test_booking_sends_owner_email_when_configured(self):
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
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("New booking inquiry", mail.outbox[0].subject)

    @override_settings(
        STORAGES={
            "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
            "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
        }
    )
    def test_home_renders_admin_packages(self):
        Package.objects.create(
            name="Gold Wedding",
            price_label="Custom",
            description="Photo and video coverage",
            features="Photography\nCinematic video",
            active=True,
            sort_order=1,
        )

        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gold Wedding")

    def test_track_click_records_lead_click(self):
        response = self.client.post(
            "/track-click/",
            {"type": LeadClick.TYPE_WHATSAPP, "page": "/"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(LeadClick.objects.count(), 1)

    def test_seo_page_renders(self):
        response = self.client.get("/seo/wedding-photographer-pratapgarh/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Wedding Photographer in Pratapgarh")

    def test_availability_reports_existing_active_booking(self):
        Booking.objects.create(
            name="Amit",
            phone="9936759702",
            event="Wedding",
            event_date="2026-12-01",
            event_date_value="2026-12-01",
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
            event_date_value="2026-12-01",
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

    def test_chatbot_uses_custom_training_keywords_first(self):
        ChatData.objects.create(
            question="custom price answer",
            keywords="price, rate, charge",
            answer="Hamare custom package ke liye WhatsApp par final quote milega.",
            priority=1,
        )

        response = self.client.post(
            "/chatbot/",
            data=json.dumps({"message": "wedding price kya hai"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["reply"],
            "Hamare custom package ke liye WhatsApp par final quote milega.",
        )

    def test_chatbot_ignores_inactive_training(self):
        ChatData.objects.create(
            question="booking",
            keywords="booking",
            answer="Inactive answer",
            active=False,
        )

        response = self.client.post(
            "/chatbot/",
            data=json.dumps({"message": "booking kaise hogi"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.json()["reply"], "Inactive answer")

    def test_logged_in_admin_can_update_booking_status(self):
        User.objects.create_user(username="admin", password="pass12345", is_staff=True)
        self.client.login(username="admin", password="pass12345")
        booking = Booking.objects.create(
            name="Amit",
            phone="9936759702",
            event="Wedding",
            event_date="2026-12-01",
            event_date_value="2026-12-01",
        )

        response = self.client.post(
            f"/dashboard/bookings/{booking.id}/status/",
            {"status": Booking.STATUS_CONFIRMED},
        )

        self.assertEqual(response.status_code, 200)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.STATUS_CONFIRMED)

    def test_logged_in_admin_can_update_booking_details(self):
        User.objects.create_user(username="admin", password="pass12345", is_staff=True)
        self.client.login(username="admin", password="pass12345")
        booking = Booking.objects.create(
            name="Amit",
            phone="9936759702",
            event="Wedding",
            event_date="2026-12-01",
            event_date_value="2026-12-01",
        )

        response = self.client.post(
            f"/dashboard/bookings/{booking.id}/details/",
            {
                "advance_amount": "5000",
                "total_amount": "15000",
                "payment_status": "Advance Paid",
                "lead_source": "Google",
                "follow_up_date": "2026-11-20",
                "notes": "Call again next week",
            },
        )

        self.assertEqual(response.status_code, 200)
        booking.refresh_from_db()
        self.assertEqual(booking.advance_amount, 5000)
        self.assertEqual(booking.total_amount, 15000)
        self.assertEqual(booking.balance_amount, 10000)
        self.assertEqual(booking.payment_status, "Advance Paid")
        self.assertEqual(booking.lead_source, "Google")
        self.assertEqual(str(booking.follow_up_date), "2026-11-20")
        self.assertEqual(booking.notes, "Call again next week")

    def test_logged_in_admin_can_export_bookings_csv(self):
        User.objects.create_user(username="admin", password="pass12345", is_staff=True)
        self.client.login(username="admin", password="pass12345")
        Booking.objects.create(
            name="Amit",
            phone="9936759702",
            event="Wedding",
            event_date="2026-12-01",
            event_date_value="2026-12-01",
        )

        response = self.client.get("/dashboard/export/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn(b"Amit", response.content)

    def test_logged_in_admin_can_export_backup_json(self):
        User.objects.create_user(username="admin", password="pass12345", is_staff=True)
        self.client.login(username="admin", password="pass12345")
        Booking.objects.create(
            name="Amit",
            phone="9936759702",
            event="Wedding",
            event_date="2026-12-01",
            event_date_value="2026-12-01",
        )

        response = self.client.get("/dashboard/backup/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertIn(b"main.booking", response.content)

    def test_non_staff_user_cannot_access_dashboard(self):
        User.objects.create_user(username="viewer", password="pass12345", is_staff=False)
        self.client.login(username="viewer", password="pass12345")

        response = self.client.get("/dashboard/")

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("admin:login"), response["Location"])


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

    @override_settings(ADMIN_SECURITY_CODE="123456", ADMIN_TOTP_SECRET="")
    def test_admin_security_code_gate_protects_dashboard(self):
        User.objects.create_user(username="admin", password="pass12345", is_staff=True)
        self.client.login(username="admin", password="pass12345")

        response = self.client.get("/dashboard/")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/security-code/", response["Location"])

    @override_settings(ADMIN_SECURITY_CODE="123456", ADMIN_TOTP_SECRET="")
    def test_admin_security_code_allows_dashboard_after_verification(self):
        User.objects.create_user(username="admin", password="pass12345", is_staff=True)
        self.client.login(username="admin", password="pass12345")

        response = self.client.post(
            "/security-code/",
            {"code": "123456", "next": "/dashboard/"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/dashboard/")
        self.assertTrue(self.client.session["admin_second_factor_ok"])
