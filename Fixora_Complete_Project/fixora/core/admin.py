from django.contrib import admin

from .models import Booking, ProviderProfile, ServiceCategory, ServiceListing


@admin.action(description="Approve selected providers")
def approve_providers(modeladmin, request, queryset):
    queryset.update(verification_status=ProviderProfile.Status.APPROVED)


@admin.action(description="Reject selected providers")
def reject_providers(modeladmin, request, queryset):
    queryset.update(verification_status=ProviderProfile.Status.REJECTED)


@admin.register(ProviderProfile)
class ProviderProfileAdmin(admin.ModelAdmin):
    list_display = ("business_name", "user", "service_area", "verification_status", "is_demo")
    list_filter = ("verification_status", "is_demo")
    search_fields = ("business_name", "user__username")
    actions = [approve_providers, reject_providers]


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(ServiceListing)
class ServiceListingAdmin(admin.ModelAdmin):
    list_display = ("title", "provider", "category", "starting_price", "is_active")
    list_filter = ("is_active", "category")
    search_fields = ("title", "provider__business_name")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "provider", "service", "scheduled_at", "status")
    list_filter = ("status",)
    search_fields = ("customer__username", "provider__business_name")
