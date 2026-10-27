from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import BookingForm, RegisterForm
from .models import Booking, ProviderProfile, ServiceCategory, ServiceListing

PROVIDER_ACTIONS = {
    "accept": Booking.Status.ACCEPTED,
    "reject": Booking.Status.REJECTED,
    "start": Booking.Status.IN_PROGRESS,
    "complete": Booking.Status.COMPLETED,
}


def _provider_or_none(user):
    """Return the user's ProviderProfile, or None for customers."""
    if not user.is_authenticated:
        return None
    return getattr(user, "provider_profile", None)


def home(request):
    categories = ServiceCategory.objects.all()
    featured = ProviderProfile.objects.filter(
        verification_status=ProviderProfile.Status.APPROVED
    )[:6]
    return render(request, "home.html", {"categories": categories, "featured": featured})


def search(request):
    qs = ServiceListing.objects.select_related("provider", "category").filter(
        is_active=True,
        provider__verification_status=ProviderProfile.Status.APPROVED,
    )
    q = request.GET.get("q", "").strip()
    cat = request.GET.get("category", "").strip()
    area = request.GET.get("area", "").strip()
    max_price = request.GET.get("max_price", "").strip()
    sort = request.GET.get("sort", "")

    if q:
        qs = qs.filter(
            Q(title__icontains=q) | Q(description__icontains=q) | Q(category__name__icontains=q)
        )
    if cat.isdigit():
        qs = qs.filter(category_id=int(cat))
    if area:
        qs = qs.filter(provider__service_area__icontains=area)
    if max_price:
        try:
            qs = qs.filter(starting_price__lte=Decimal(max_price))
        except (InvalidOperation, ValueError):
            messages.error(request, "Enter a valid maximum price.")

    if sort == "price_asc":
        qs = qs.order_by("starting_price")
    elif sort == "price_desc":
        qs = qs.order_by("-starting_price")
    else:
        qs = qs.order_by("title")

    page_obj = Paginator(qs, 9).get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)

    return render(request, "search.html", {
        "page_obj": page_obj,
        "categories": ServiceCategory.objects.all(),
        "q": q,
        "selected_category": cat,
        "area": area,
        "max_price": max_price,
        "sort": sort,
        "query_string": params.urlencode(),
    })


def provider_detail(request, pk):
    provider = get_object_or_404(ProviderProfile, pk=pk)
    is_owner = request.user.is_authenticated and provider.user_id == request.user.id
    if not (provider.is_approved or is_owner):
        raise Http404("Provider not found")
    services = provider.services.filter(is_active=True).select_related("category")
    return render(request, "provider_detail.html", {"provider": provider, "services": services})


@login_required
def book_service(request, pk):
    service = get_object_or_404(
        ServiceListing.objects.select_related("provider"), pk=pk, is_active=True
    )
    if _provider_or_none(request.user):
        messages.error(request, "Provider accounts cannot book services.")
        return redirect("provider_detail", pk=service.provider_id)
    if not service.provider.is_approved:
        raise Http404("This provider is not available for booking.")

    if request.method == "POST":
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.customer = request.user
            booking.provider = service.provider
            booking.service = service
            booking.quoted_price = service.starting_price
            try:
                with transaction.atomic():
                    booking.save()
            except IntegrityError:
                form.add_error(
                    "scheduled_at",
                    "This provider already has a booking at that time. Please choose another slot.",
                )
            else:
                messages.success(request, "Booking request sent. The provider will confirm it.")
                return redirect("booking_detail", pk=booking.pk)
    else:
        form = BookingForm()

    return render(request, "book.html", {"service": service, "form": form})


@login_required
def dashboard(request):
    provider = _provider_or_none(request.user)
    if provider:
        bookings = provider.bookings.select_related("service", "customer").order_by("scheduled_at")
        return render(request, "dashboard.html", {"provider": provider, "bookings": bookings})
    bookings = request.user.bookings.select_related("service", "provider").order_by("-scheduled_at")
    return render(request, "dashboard.html", {"bookings": bookings})


@login_required
def booking_detail(request, pk):
    provider = _provider_or_none(request.user)
    # Only the customer who made the booking or the provider it belongs to may view it.
    booking = get_object_or_404(
        Booking.objects.select_related("service", "provider", "customer").filter(
            Q(customer=request.user) | Q(provider=provider) if provider else Q(customer=request.user)
        ),
        pk=pk,
    )
    is_customer = booking.customer_id == request.user.id
    can_cancel = is_customer and booking.status in (
        Booking.Status.PENDING,
        Booking.Status.ACCEPTED,
    )
    return render(request, "booking_detail.html", {
        "booking": booking,
        "is_customer": is_customer,
        "can_cancel": can_cancel,
    })


@login_required
@require_POST
def cancel_booking(request, pk):
    booking = get_object_or_404(Booking, pk=pk, customer=request.user)
    if booking.can_transition_to(Booking.Status.CANCELLED):
        booking.status = Booking.Status.CANCELLED
        booking.save(update_fields=["status", "updated_at"])
        messages.success(request, "Booking cancelled.")
    else:
        messages.error(request, "This booking can no longer be cancelled.")
    return redirect("booking_detail", pk=pk)


@login_required
@require_POST
def provider_update_booking(request, pk, action):
    provider = _provider_or_none(request.user)
    if provider is None or action not in PROVIDER_ACTIONS:
        raise Http404
    if not provider.is_approved:
        messages.error(request, "Your provider account must be approved before you can manage bookings.")
        return redirect("dashboard")

    target = PROVIDER_ACTIONS[action]
    with transaction.atomic():
        # Filtering by provider means a provider can never touch another provider's booking.
        booking = get_object_or_404(
            Booking.objects.select_for_update(), pk=pk, provider=provider
        )
        if booking.can_transition_to(target):
            booking.status = target
            booking.save(update_fields=["status", "updated_at"])
            messages.success(request, f"Booking is now {booking.get_status_display()}.")
        else:
            messages.error(
                request, f"A {booking.get_status_display().lower()} booking cannot be changed this way."
            )
    return redirect("dashboard")


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save()
                if form.cleaned_data["is_provider"]:
                    ProviderProfile.objects.create(
                        user=user,
                        business_name=form.cleaned_data["business_name"],
                        service_area=form.cleaned_data["service_area"],
                    )
            login(request, user)
            messages.success(request, "Welcome to Fixora!")
            return redirect("dashboard")
    else:
        form = RegisterForm()
    return render(request, "register.html", {"form": form})
