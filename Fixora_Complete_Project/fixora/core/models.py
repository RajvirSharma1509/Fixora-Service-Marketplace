from django.conf import settings
from django.db import models
from django.db.models import Q

# Booking statuses that occupy a provider's time slot.
ACTIVE_BOOKING_STATUSES = ("pending", "accepted", "in_progress")


class ServiceCategory(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "service categories"

    def __str__(self):
        return self.name


class ProviderProfile(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending verification"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="provider_profile",
    )
    business_name = models.CharField(max_length=120)
    bio = models.TextField(blank=True)
    service_area = models.CharField(max_length=120, help_text="Area or city this provider serves")
    experience_years = models.PositiveSmallIntegerField(default=0)
    verification_status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING
    )
    is_demo = models.BooleanField(default=False, help_text="Sample data for demonstration only")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["business_name"]

    def __str__(self):
        return self.business_name

    @property
    def is_approved(self):
        return self.verification_status == self.Status.APPROVED


class ServiceListing(models.Model):
    class PricingMethod(models.TextChoices):
        PER_VISIT = "per_visit", "per visit"
        PER_HOUR = "per_hour", "per hour"
        PER_JOB = "per_job", "per job"

    provider = models.ForeignKey(ProviderProfile, on_delete=models.CASCADE, related_name="services")
    category = models.ForeignKey(ServiceCategory, on_delete=models.PROTECT, related_name="services")
    title = models.CharField(max_length=120)
    description = models.TextField()
    starting_price = models.DecimalField(max_digits=10, decimal_places=2)
    pricing_method = models.CharField(
        max_length=20, choices=PricingMethod.choices, default=PricingMethod.PER_VISIT
    )
    is_active = models.BooleanField(
        default=True, help_text="Deactivate instead of deleting so booking history is kept"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return f"{self.title} ({self.provider})"


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"
        IN_PROGRESS = "in_progress", "In progress"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    # Allowed status changes. Anything not listed here is rejected.
    TRANSITIONS = {
        Status.PENDING: {Status.ACCEPTED, Status.REJECTED, Status.CANCELLED},
        Status.ACCEPTED: {Status.IN_PROGRESS, Status.CANCELLED},
        Status.IN_PROGRESS: {Status.COMPLETED},
    }

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="bookings"
    )
    provider = models.ForeignKey(ProviderProfile, on_delete=models.PROTECT, related_name="bookings")
    service = models.ForeignKey(ServiceListing, on_delete=models.PROTECT, related_name="bookings")
    scheduled_at = models.DateTimeField()
    address = models.TextField()
    problem = models.TextField()
    quoted_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Starting price when booked. This is an estimate, not a final quote.",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-scheduled_at"]
        constraints = [
            # The database itself prevents two active bookings for the same provider and time.
            models.UniqueConstraint(
                fields=["provider", "scheduled_at"],
                condition=Q(status__in=ACTIVE_BOOKING_STATUSES),
                name="unique_active_booking_slot",
            ),
        ]

    def __str__(self):
        return f"Booking #{self.pk} - {self.service.title}"

    def can_transition_to(self, new_status):
        return new_status in self.TRANSITIONS.get(self.status, set())
