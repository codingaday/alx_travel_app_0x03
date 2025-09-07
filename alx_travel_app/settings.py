"""

Django settings for alx_travel_app project.

"""

import os  # IMPORTANT: os is needed for STATIC_ROOT

import environ

from pathlib import Path


# Build paths inside the project like this: BASE_DIR / 'subdir'.

BASE_DIR = Path(__file__).resolve().parent.parent


# Use django-environ to manage all environment variables

env = environ.Env(
    DEBUG=(bool, False)  # Cast DEBUG to a boolean, default to False
)


# Reading .env file

environ.Env.read_env(BASE_DIR / ".env")


# --- Core Security Settings ---


# Get the SECRET_KEY from the environment. Render will provide this.

SECRET_KEY = env("SECRET_KEY")


# Get DEBUG value. This will be False on Render.

DEBUG = env.bool("DEBUG", default=False)


# Get ALLOWED_HOSTS from Render's environment variable.

# For local dev, you can set ALLOWED_HOSTS=.env in your .env file

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

RENDER_EXTERNAL_HOSTNAME = env.str("RENDER_EXTERNAL_HOSTNAME", default=None)

if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)


# --- Application Definition ---


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",  # For development with whitenoise
    "django.contrib.staticfiles",
    # Third-party apps
    "rest_framework",
    "corsheaders",
    "drf_yasg",
    # My Apps
    "alx_travel_app.listings.apps.ListingsConfig",
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # Whitenoise middleware
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "alx_travel_app.urls"


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth", 
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


WSGI_APPLICATION = "alx_travel_app.wsgi.application"


# --- Database ---

# This is much cleaner. django-environ's env.db() will automatically parse

# the DATABASE_URL environment variable provided by Render.

DATABASES = {
    "default": env.db(default="postgresql://postgres:postgres@localhost:5432/mysite")
}


AUTH_USER_MODEL = "listings.User"


# --- Password validation, Internationalization, etc. ---

# (These sections are fine and do not need changes)

AUTH_PASSWORD_VALIDATORS = [...]

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# --- Static files (CSS, JavaScript, Images) ---

STATIC_URL = "/static/"

# This tells Django where to collect all static files for production

STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")


# Enable WhiteNoise's storage backend for compressing and caching static files.

# This only runs when DEBUG is False (i.e., in production).

if not DEBUG:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# --- DRF and CORS Settings ---

REST_FRAMEWORK = {"DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"]}

CORS_ALLOW_ALL_ORIGINS = True


# --- Celery Configuration ---

# SWITCH FROM RABBITMQ TO REDIS for Render's managed service

# This line will automatically use the REDIS_URL from Render's environment.

# For local dev, it falls back to the default redis://localhost.

CELERY_BROKER_URL = env("REDIS_URL", default="redis://localhost:6379/0")


CELERY_RESULT_BACKEND = "rpc://"  # This can be switched to Redis too if needed

CELERY_ACCEPT_CONTENT = ["json"]

CELERY_TASK_SERIALIZER = "json"

CELERY_RESULT_SERIALIZER = "json"

CELERY_TIMEZONE = "UTC"


# --- Email Configuration ---

# For development, the console backend is easiest.

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


# --- Production Security Settings ---

# These settings will only be applied when DEBUG is False (production)

if not DEBUG:
    CSRF_COOKIE_SECURE = True

    SESSION_COOKIE_SECURE = True

    SECURE_SSL_REDIRECT = True

    SECURE_HSTS_SECONDS = 3600

    SECURE_HSTS_INCLUDE_SUBDOMAINS = True

    SECURE_HSTS_PRELOAD = True

CELERY_TASK_TRACK_STARTED = True

CELERY_TASK_TIME_LIMIT = 300  # seconds
# For development, the console backend is easiest. It just prints emails to your terminal.

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


# For production, you would use SMTP:

# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# EMAIL_HOST = 'smtp.your-email-provider.com'

# EMAIL_PORT = 587

# EMAIL_USE_TLS = True

# EMAIL_HOST_USER = 'your-email@example.com'
