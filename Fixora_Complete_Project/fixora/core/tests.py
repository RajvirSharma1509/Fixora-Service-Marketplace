from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Booking, ProviderProfile, ServiceCategory, ServiceListing

PASSWORD = "StrongPass!12345"


class FixoraTests(TestCase):
    def setUp(self):
        self.cat = ServiceCategory.objects.create(name="Plumbing", slug="plumbing")
        self.provider_user = User.objects.create_user("prov", password=PASSWORD)
        self.provider = ProviderProfile.objects.create(
            user=self.provider_user, business_name="Test Plumbers", service_area="Area 1",
            verification_status=ProviderProfile.Status.APPROVED,
        )
        self.service = ServiceListing.objects.create(
            provider=self.provider, category=self.cat, title="Leak fix",
            description="Fix leaks", starting_price=Decimal("299"),
        )
        self.customer = User.objects.create_user("cust", password=PASSWORD)
        self.other_customer = User.objects.create_user("other", password=PASSWORD)
        self.other_provider_user = User.objects.create_user("prov2", password=PASSWORD)
        self.other_provider = ProviderProfile.objects.create(
            user=self.other_provider_user, business_name="Other Co", service_area="Area 2",
            verification_status=ProviderProfile.Status.APPROVED,
        )
        self.when = (timezone.now() + timedelta(days=2)).replace(second=0, microsecond=0)

    def make_booking(self, **overrides):
        data = dict(
            customer=self.customer, provider=self.provider, service=self.service,
            scheduled_at=self.when, address="Flat 1", problem="Leaking tap",
            quoted_price=self.service.starting_price,
        )
        data.update(overrides)
        return Booking.objects.create(**data)

    def test_registration_creates_pending_provider(self):
        resp = self.client.post(reverse("register"), {
            "username": "newprov", "email": "n@example.com",
            "password1": "ComplexPass!98765", "password2": "ComplexPass!98765",
            "is_provider": True, "business_name": "New Co", "service_area": "Area 3",
        })
        self.assertRedirects(resp, reverse("dashboard"))
        profile = ProviderProfile.objects.get(user__username="newprov")
        self.assertEqual(profile.verification_status, ProviderProfile.Status.PENDING)

    def test_unapproved_provider_cannot_be_booked(self):
        self.provider.verification_status = ProviderProfile.Status.PENDING
        self.provider.save()
        self.client.login(username="cust", password=PASSWORD)
        resp = self.client.get(reverse("book_service", args=[self.service.pk]))
        self.assertEqual(resp.status_code, 404)

    def test_booking_creation_and_slot_conflict(self):
        self.client.login(username="cust", password=PASSWORD)
        local_when = timezone.localtime(self.when).strftime("%Y-%m-%dT%H:%M")
        form_data = {"scheduled_at": local_when, "address": "Flat 1", "problem": "Tap leaks"}
        url = reverse("book_service", args=[self.service.pk])

        resp = self.client.post(url, form_data)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Booking.objects.count(), 1)

        resp = self.client.post(url, form_data)  # same provider, same slot
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Booking.objects.count(), 1)

    def test_past_date_is_rejected(self):
        self.client.login(username="cust", password=PASSWORD)
        past = timezone.localtime(timezone.now() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")
        resp = self.client.post(reverse("book_service", args=[self.service.pk]), {
            "scheduled_at": past, "address": "Flat 1", "problem": "Tap leaks",
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Booking.objects.count(), 0)

    def test_customer_cannot_view_other_customers_booking(self):
        booking = self.make_booking()
        self.client.login(username="other", password=PASSWORD)
        resp = self.client.get(reverse("booking_detail", args=[booking.pk]))
        self.assertEqual(resp.status_code, 404)

    def test_provider_accepts_booking(self):
        booking = self.make_booking()
        self.client.login(username="prov", password=PASSWORD)
        self.client.post(reverse("provider_update_booking", args=[booking.pk, "accept"]))
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.ACCEPTED)

    def test_provider_cannot_act_on_another_providers_booking(self):
        booking = self.make_booking()
        self.client.login(username="prov2", password=PASSWORD)
        resp = self.client.post(reverse("provider_update_booking", args=[booking.pk, "accept"]))
        self.assertEqual(resp.status_code, 404)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.PENDING)

    def test_invalid_transition_is_blocked(self):
        booking = self.make_booking()  # pending cannot jump straight to completed
        self.client.login(username="prov", password=PASSWORD)
        self.client.post(reverse("provider_update_booking", args=[booking.pk, "complete"]))
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.PENDING)

    def test_customer_can_cancel_own_pending_booking(self):
        booking = self.make_booking()
        self.client.login(username="cust", password=PASSWORD)
        self.client.post(reverse("cancel_booking", args=[booking.pk]))
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.CANCELLED)

    def test_search_filters_by_max_price(self):
        ServiceListing.objects.create(
            provider=self.provider, category=self.cat, title="Pricey job",
            description="Expensive", starting_price=Decimal("999"),
        )
        resp = self.client.get(reverse("search"), {"max_price": "500"})
        titles = [s.title for s in resp.context["page_obj"]]
        self.assertEqual(titles, ["Leak fix"])
