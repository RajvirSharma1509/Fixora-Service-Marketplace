# Fixora: Hyperlocal Service Marketplace

Find Trusted Services Near You.

Fixora connects customers with independent local service providers. Customers search services, view provider profiles, and send booking requests. Providers accept, reject, start, and complete bookings. Administrators approve providers through Django Admin.

> **Status:** Core version. Working: search, provider pages, customer registration and login, booking with slot-conflict protection, provider booking actions with status rules, customer cancellation, role-based access, Django Admin, demo data loader. Not yet built: reviews, favourites, notifications, complaints, payments, availability calendar, password reset, profile editing. See "Limitations".

## Technology
- Python 3.12+ and Django 5.2 (LTS)
- SQLite for local development
- Django templates with a local CSS file (no external CDN)

## Windows setup (PowerShell)

Run these commands in PowerShell from inside the `fixora` folder.

```powershell
# 1. Create and activate a virtual environment
py -m venv venv
.\venv\Scripts\Activate.ps1
# If activation is blocked, run this once, then activate again:
# Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create the database tables (migrations are generated from the models)
python manage.py makemigrations core
python manage.py migrate

# 4. Create an admin account (you choose the username and password)
python manage.py createsuperuser

# 5. Load demonstration data (clearly labelled [DEMO])
python manage.py seed_demo

# 6. Start the server
python manage.py runserver
```

Open http://127.0.0.1:8000 in your browser. Django Admin is at http://127.0.0.1:8000/admin/.

Optional: set a real secret key for your own runs.
```powershell
$env:DJANGO_SECRET_KEY = "paste-a-long-random-string-here"
```

## Demo walkthrough
1. Register a **customer** account (leave "I want to offer services" unticked). Search for a service and book it.
2. Register a **provider** account (tick the box, enter a business name and area). Your provider account starts as *Pending*.
3. Log in to Django Admin as the superuser, open **Provider profiles**, select your provider, and run the **Approve selected providers** action.
4. Log in as the provider, open the dashboard, and accept the booking. Then start and complete it.

Keep separate browser windows (or a private window) for each role.

## Run the tests
```powershell
python manage.py test core
```

## Project layout
```
fixora/
  manage.py
  requirements.txt
  config/            settings, root URLs, WSGI/ASGI
  core/
    models.py        ServiceCategory, ProviderProfile, ServiceListing, Booking
    views.py         public pages, booking, dashboard, provider actions
    forms.py         BookingForm (future-date check), RegisterForm
    admin.py         Django Admin with approve/reject actions
    urls.py          URL routes
    tests.py         automated tests
    management/commands/seed_demo.py   demo data loader
  templates/         HTML templates
  static/css/        style.css
```

## Database overview
- **ServiceCategory**: name and slug.
- **ProviderProfile**: one per provider user (`OneToOne` with the Django user). Holds `verification_status` (pending, approved, rejected).
- **ServiceListing**: a service offered by a provider. Has a starting price and pricing method. Deactivate it with `is_active`. Never delete it, so booking history stays intact.
- **Booking**: links customer, provider, and service. Stores the price shown at booking time (`quoted_price`) as an estimate. Status follows fixed transitions (see below).

**Slot protection:** a database `UniqueConstraint` allows only one active booking (pending, accepted, or in progress) per provider and exact date-time. Two customers cannot book the same slot, even if they submit at the same moment.

**Booking status rules**
- Pending: accept, reject, or cancel
- Accepted: start work, or cancel
- In progress: mark completed
- Rejected, completed, and cancelled bookings cannot change.

## Security notes
- Passwords are hashed by Django's built-in authentication.
- Every page that shows booking data checks ownership on the server. Customers see only their own bookings. Providers see only bookings assigned to them. Other requests return 404.
- Forms and POST actions use Django's CSRF protection.
- The secret key comes from the `DJANGO_SECRET_KEY` environment variable. Do not commit real keys.
- Demo providers are marked `is_demo` and cannot log in.

## Limitations (honest status)
- SQLite is for local demo use. For production, switch the `DATABASES` setting to MySQL or PostgreSQL.
- No payments are processed. Price shown is a starting estimate, not a final quote.
- Ratings, reviews, favourites, notifications, complaints, and password reset are not yet implemented.
- Location filtering is a text match on service area. There is no GPS or maps feature.
- No email is sent.
- Demo providers are sample data and are not verified businesses.

## Future scope
Reviews after completed bookings, provider availability calendar, payment records with a demo mode, notifications, complaint handling, password reset by email, profile editing, and a payment gateway in test mode.

## Screenshots
Add screenshots to a `docs/screenshots/` folder after running the app, then link them here.

## Team
Add your name and team members here.
