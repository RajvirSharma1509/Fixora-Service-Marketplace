# Initial database schema for Fixora.
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name='ServiceCategory',
            fields=[('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')), ('name', models.CharField(max_length=80, unique=True)), ('slug', models.SlugField(max_length=100, unique=True))],
            options={'ordering': ['name'], 'verbose_name_plural': 'service categories'},
        ),
        migrations.CreateModel(
            name='ProviderProfile',
            fields=[('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')), ('business_name', models.CharField(max_length=120)), ('bio', models.TextField(blank=True)), ('service_area', models.CharField(help_text='Area or city this provider serves', max_length=120)), ('experience_years', models.PositiveSmallIntegerField(default=0)), ('verification_status', models.CharField(choices=[('pending', 'Pending verification'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending', max_length=10)), ('is_demo', models.BooleanField(default=False, help_text='Sample data for demonstration only')), ('created_at', models.DateTimeField(auto_now_add=True)), ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='provider_profile', to=settings.AUTH_USER_MODEL))],
            options={'ordering': ['business_name']},
        ),
        migrations.CreateModel(
            name='ServiceListing',
            fields=[('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')), ('title', models.CharField(max_length=120)), ('description', models.TextField()), ('starting_price', models.DecimalField(decimal_places=2, max_digits=10)), ('pricing_method', models.CharField(choices=[('per_visit', 'per visit'), ('per_hour', 'per hour'), ('per_job', 'per job')], default='per_visit', max_length=20)), ('is_active', models.BooleanField(default=True, help_text='Deactivate instead of deleting so booking history is kept')), ('created_at', models.DateTimeField(auto_now_add=True)), ('updated_at', models.DateTimeField(auto_now=True)), ('category', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='services', to='core.servicecategory')), ('provider', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='services', to='core.providerprofile'))],
            options={'ordering': ['title']},
        ),
        migrations.CreateModel(
            name='Booking',
            fields=[('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')), ('scheduled_at', models.DateTimeField()), ('address', models.TextField()), ('problem', models.TextField()), ('quoted_price', models.DecimalField(decimal_places=2, help_text='Starting price when booked. This is an estimate, not a final quote.', max_digits=10)), ('status', models.CharField(choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected'), ('in_progress', 'In progress'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='pending', max_length=20)), ('created_at', models.DateTimeField(auto_now_add=True)), ('updated_at', models.DateTimeField(auto_now=True)), ('customer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='bookings', to=settings.AUTH_USER_MODEL)), ('provider', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='bookings', to='core.providerprofile')), ('service', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='bookings', to='core.servicelisting'))],
            options={'ordering': ['-scheduled_at']},
        ),
        migrations.AddConstraint(
            model_name='booking',
            constraint=models.UniqueConstraint(condition=models.Q(('status__in', ('pending', 'accepted', 'in_progress'))), fields=('provider', 'scheduled_at'), name='unique_active_booking_slot'),
        ),
    ]
