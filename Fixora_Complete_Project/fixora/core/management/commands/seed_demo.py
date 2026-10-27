from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from core.models import ProviderProfile, ServiceCategory, ServiceListing

CATEGORIES = [
    "Plumbing", "Electrical Repair", "Home Cleaning", "AC Repair", "Computer and Laptop Repair",
    "Mechanics", "Home Tutoring", "Painting", "Carpentry", "Appliance Repair",
]

# All providers below are DEMONSTRATION data, flagged with is_demo=True and a [DEMO] prefix.
DEMO_PROVIDERS = [
    {
        "username": "demo_plumber",
        "business_name": "[DEMO] Sample Plumbing Co.",
        "service_area": "Demo Area 1",
        "experience_years": 8,
        "bio": "Demonstration provider profile. Not a real business.",
        "services": [
            ("Plumbing", "Pipe leak repair", "Fixing leaking taps, pipes and joints.", "299", "per_visit"),
        ],
    },
    {
        "username": "demo_electrician",
        "business_name": "[DEMO] Sample Electric Services",
        "service_area": "Demo Area 2",
        "experience_years": 5,
        "bio": "Demonstration provider profile. Not a real business.",
        "services": [
            ("Electrical Repair", "Switch and socket repair", "Replacing faulty switches and sockets.", "249", "per_visit"),
            ("AC Repair", "AC service and gas top-up", "Cleaning and servicing split ACs.", "799", "per_job"),
        ],
    },
    {
        "username": "demo_laptop",
        "business_name": "[DEMO] Sample Laptop Clinic",
        "service_area": "Demo Area 1",
        "experience_years": 4,
        "bio": "Demonstration provider profile. Not a real business.",
        "services": [
            ("Computer and Laptop Repair", "Laptop screen replacement", "Diagnosis and screen replacement.", "1499", "per_job"),
        ],
    },
]


class Command(BaseCommand):
    help = "Load clearly labelled DEMO categories, providers and services."

    def handle(self, *args, **options):
        for name in CATEGORIES:
            ServiceCategory.objects.get_or_create(name=name, defaults={"slug": slugify(name)})

        for data in DEMO_PROVIDERS:
            user, created = User.objects.get_or_create(username=data["username"])
            if created:
                user.set_unusable_password()  # demo providers cannot log in
                user.save()
            provider, _ = ProviderProfile.objects.update_or_create(
                user=user,
                defaults={
                    "business_name": data["business_name"],
                    "service_area": data["service_area"],
                    "experience_years": data["experience_years"],
                    "bio": data["bio"],
                    "verification_status": ProviderProfile.Status.APPROVED,
                    "is_demo": True,
                },
            )
            for cat_name, title, description, price, method in data["services"]:
                ServiceListing.objects.update_or_create(
                    provider=provider,
                    title=title,
                    defaults={
                        "category": ServiceCategory.objects.get(name=cat_name),
                        "description": description,
                        "starting_price": Decimal(price),
                        "pricing_method": method,
                        "is_active": True,
                    },
                )

        self.stdout.write(self.style.SUCCESS("Demo data loaded (all entries are marked as DEMO)."))
