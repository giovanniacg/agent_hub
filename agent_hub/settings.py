import environ
from pathlib import Path


# -------------------------------------------------------
# BASE SETTINGS                                        #
# -------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    SECRET_KEY=(
        str,
        "django-insecure-i1e*2gyrle6c6c!36nh@@m8*$x+nyr6-s^4ai$39knh6ju^8ot",
    ),
    ALLOWED_HOSTS=(list, ["*"]),
    DATABASE_NAME=(str, "db.sqlite3"),
    DATABASE_USER=(str, "user"),
    DATABASE_PASSWORD=(str, "password"),
    DATABASE_HOST=(str, "localhost"),
    DATABASE_PORT=(int, 5432),
    USE_POSTGRES=(bool, False),
    API_KEY_PEPPER=(str, "unsafe-default-pepper"),
    DECIDIM_EMAIL=(str, "email@example.com"),
    DECIDIM_PASSWORD=(str, "password123"),
    DECIDIM_BASE_URL=(str, "https://lab-decide.dataprev.gov.br"),
)

ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    environ.Env.read_env(str(ENV_FILE))


SECRET_KEY = env("SECRET_KEY")

DEBUG = env("DEBUG")

ALLOWED_HOSTS = env("ALLOWED_HOSTS")


# -------------------------------------------------------
# APPLICATION DEFINITION                               #
# -------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party apps
    "rest_framework",
    "rest_framework.authtoken",
    "drf_spectacular",
    "django_filters",
    "whitenoise.runserver_nostatic",
    # Local apps
    "core",
    "api",
    "telegram",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "agent_hub.urls"
WSGI_APPLICATION = "agent_hub.wsgi.application"


# -------------------------------------------------------
# TEMPLATES SETTINGS                                   #
# -------------------------------------------------------

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

# -------------------------------------------------------
# DATABASE SETTINGS                                     #
# -------------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    },
    "postgres": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DATABASE_NAME"),
        "USER": env("DATABASE_USER"),
        "PASSWORD": env("DATABASE_PASSWORD"),
        "HOST": env("DATABASE_HOST"),
        "PORT": env("DATABASE_PORT"),
    },
}

# Swap to Postgres when requested (e.g. inside docker-compose)
if env("USE_POSTGRES"):
    DATABASES["default"] = DATABASES["postgres"].copy()


# -------------------------------------------------------
# PASSWORD VALIDATION                                  #
# -------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# -------------------------------------------------------
# INTERNATIONALIZATION                                  #
# -------------------------------------------------------

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# -------------------------------------------------------
# DJANGO REST FRAMEWORK SETTINGS                        #
# -------------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "api.auth.APIKeyAuthentication",
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

API_KEY_PEPPER = env("API_KEY_PEPPER")


# -------------------------------------------------------
# SPECTACULAR SETTINGS                                 #
# -------------------------------------------------------
SPECTACULAR_SETTINGS = {
    "TITLE": "API Documentation",
    "DESCRIPTION": "API endpoints for the agent hub",
    "VERSION": "1.0.0",
    "SCHEMA_PATH": "/api/schema/",
    "SECURITY": [
        {"XApiKey": []},
        {"BearerAuth": []},
        {"cookieAuth": []},
    ],
    "SWAGGER_UI_SETTINGS": {
        "persistAuthorization": True,
    },
}


# -------------------------------------------------------
# STATIC FILES SETTINGS                                 #
# -------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}


# -------------------------------------------------------
# DEICIDIM SETTINGS                                     #
# -------------------------------------------------------

DECIDIM_EMAIL = env("DECIDIM_EMAIL")
DECIDIM_PASSWORD = env("DECIDIM_PASSWORD")
DECIDIM_BASE_URL = env("DECIDIM_BASE_URL")
