import os
from pathlib import Path
from dotenv import load_dotenv
import stripe

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "dev-unsafe")
DEBUG = os.getenv("DEBUG", "False") == "False"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost,https://eventback1.onrender.com,eventback1.onrender.com").split(",")
# ALLOWED_HOSTS = ['localhost','https://eventback1.onrender.com','eventback1.onrender.com']

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rentals",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]
WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "rentals" / "static"]
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# Payments
PAYPAL = {
    "CLIENT_ID": os.getenv("PAYPAL_CLIENT_ID", ""),
    "CLIENT_SECRET": os.getenv("PAYPAL_CLIENT_SECRET", ""),
    "MODE": os.getenv("PAYPAL_MODE", "sandbox"),  # sandbox or live
    "CURRENCY": os.getenv("PAYPAL_CURRENCY", "USD"),
}
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY", "")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
PAYSTACK_PUBLIC_KEY = os.getenv("PAYSTACK_PUBLIC_KEY", "")
PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY", "")
SITE_URL = os.getenv("SITE_URL", "http://127.0.0.1:8000,https://eventback1.onrender.com,eventback1.onrender.com")
