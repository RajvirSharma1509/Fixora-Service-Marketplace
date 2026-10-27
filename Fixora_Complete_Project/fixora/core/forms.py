from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Booking


class BookingForm(forms.ModelForm):
    scheduled_at = forms.DateTimeField(
        label="Preferred date and time",
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        input_formats=["%Y-%m-%dT%H:%M"],
    )

    class Meta:
        model = Booking
        fields = ["scheduled_at", "address", "problem"]
        labels = {"address": "Service address", "problem": "Describe the problem"}
        widgets = {
            "address": forms.Textarea(attrs={"rows": 2}),
            "problem": forms.Textarea(attrs={"rows": 3}),
        }

    def clean_scheduled_at(self):
        when = self.cleaned_data["scheduled_at"]
        if when <= timezone.now():
            raise forms.ValidationError("Choose a date and time in the future.")
        return when


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    is_provider = forms.BooleanField(
        required=False,
        label="I want to offer services (provider account, needs admin approval)",
    )
    business_name = forms.CharField(max_length=120, required=False)
    service_area = forms.CharField(max_length=120, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("is_provider"):
            if not cleaned.get("business_name"):
                self.add_error("business_name", "Required for provider accounts.")
            if not cleaned.get("service_area"):
                self.add_error("service_area", "Required for provider accounts.")
        return cleaned
