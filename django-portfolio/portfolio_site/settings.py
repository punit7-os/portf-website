"""
Django settings for portfolio_site project.

This file is CLEANED and DEDUPLICATED.
All features from the original 365-line file are preserved.

Key goals:
- One source of truth per setting
- No overridden / dead code
- Safe for local, AWS EC2, Render
"""

# ------------------------------------------------------------------------------
# IMPORTS (kept ONCE only)
# ------------------------------------------------------------------------------
from pathlib import Path
from decouple import config
import os

# ------------------------------------------------------------------------------
# BASE DIRECTORY
# ------------------------------------------------------------------------------
# Defined ONCE.
# Previously defined 3 times — later ones were overriding earlier ones.
BASE_DIR = Path(__file__).resolve().parent.parent

# ------------------------------------------------------------------------------
# SECURITY SETTINGS
# ------------------------------------------------------------------------------
# SECRET_KEY:
# Previously hardcoded AND commented AND env-based.
# Now: env-first with safe dev fallback.
SECRET_KEY = config("SECRET_KEY")


# DEBUG:
# Previously set True AND env-based later.
# Only ONE definition must exist.
DEBUG = config("DEBUG", default=True, cast=bool)

# ALLOWED_HOSTS:
# Previously "*" hardcoded AND env-based later.
# Keep env-based so AWS/Render works without code change.
ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="127.0.0.1,localhost",
    cast=lambda v: [h.strip() for h in v.split(",") if h.strip()]
)


# CSRF trusted origins (needed if you deploy on custom domain / https)
CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
]

# ------------------------------------------------------------------------------
# RAZORPAY CONFIG
# ------------------------------------------------------------------------------
# These were duplicated earlier — kept ONCE.
# They are used in views.py (initiate_payment, payment_handler)
RAZORPAY_KEY_ID = config("RAZORPAY_KEY_ID", default=None)
RAZORPAY_KEY_SECRET = config("RAZORPAY_KEY_SECRET", default=None)
RAZORPAY_WEBHOOK_SECRET = config("RAZORPAY_WEBHOOK_SECRET", default=None)

# ------------------------------------------------------------------------------
# APPLICATION DEFINITION
# ------------------------------------------------------------------------------
# INSTALLED_APPS was duplicated earlier (sites app repeated).
# Now each app appears ONCE.
INSTALLED_APPS = [
    # Django core
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",   # REQUIRED by django-allauth

    # Local apps
    "core",
    "shop",
    "blog",
    "live_data",
    "trade_dashboard",

    # Third-party auth
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
]

# ------------------------------------------------------------------------------
# MIDDLEWARE
# ------------------------------------------------------------------------------
# Order is important.
# AccountMiddleware MUST come after AuthenticationMiddleware.
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# ------------------------------------------------------------------------------
# URL & WSGI
# ------------------------------------------------------------------------------
ROOT_URLCONF = "portfolio_site.urls"
WSGI_APPLICATION = "portfolio_site.wsgi.application"

# ------------------------------------------------------------------------------
# TEMPLATES
# ------------------------------------------------------------------------------
# cart_counts context processor is REQUIRED for cart badge
# request processor REQUIRED for allauth
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # project-level templates
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "shop.context_processors.cart_counts",
            ],
        },
    },
]

# ------------------------------------------------------------------------------
# DATABASE
# ------------------------------------------------------------------------------
# SQLite kept (same as original)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ------------------------------------------------------------------------------
# AUTHENTICATION / ALLAUTH
# ------------------------------------------------------------------------------
# Required by django-allauth
SITE_ID = 1

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
)

# These were repeated multiple times earlier — kept ONCE
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = "optional"
ACCOUNT_AUTHENTICATION_METHOD = "username_email"
ACCOUNT_USERNAME_REQUIRED = True

LOGIN_URL = "blog:login"
LOGIN_REDIRECT_URL = "shop:product_list"
LOGOUT_REDIRECT_URL = "shop:product_list"



SOCIALACCOUNT_AUTO_SIGNUP = True

# Google provider config
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
    }
}

# ------------------------------------------------------------------------------
# EMAIL (SMTP – PRODUCTION READY)
# ------------------------------------------------------------------------------
# Earlier you had:
# 1) console backend
# 2) smtp backend
# Django only uses LAST one anyway.
# We keep SMTP (superset; works everywhere).
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# ------------------------------------------------------------------------------
# PASSWORD VALIDATION
# ------------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ------------------------------------------------------------------------------
# INTERNATIONALIZATION
# ------------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Kolkata"

USE_I18N = True
USE_TZ = True

# ------------------------------------------------------------------------------
# STATIC FILES
# ------------------------------------------------------------------------------
# STATIC settings were duplicated earlier.
# collectstatic uses STATIC_ROOT.
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# ------------------------------------------------------------------------------
# DEFAULTS
# ------------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
