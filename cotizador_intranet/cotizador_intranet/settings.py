import os
import sys
from pathlib import Path
from django.utils.translation import gettext_lazy as _
from dotenv import load_dotenv

# === Paths / ENV ===
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR / "apps"))
load_dotenv()  # carga .env al inicio

# === Seguridad / Debug ===
def env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in {"1", "true", "yes", "y", "on"}

SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-cambia-esto-en-produccion")
DEBUG = env_bool("DEBUG", True)

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# Producción: si usas dominio/https, agrega también (opcional):
# CSRF_TRUSTED_ORIGINS = [f"https://{h.strip()}" for h in ALLOWED_HOSTS if "." in h]

# === Apps ===
INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Terceros
    "crispy_forms",
    "crispy_bootstrap5",

    # Locales (usar AppConfig, sin duplicar)
    "apps.core.apps.CoreConfig",
    "apps.usuarios.apps.UsuariosConfig",
]

CRISPY_ALLOWED_TEMPLATE_PACKS = ["bootstrap5"]
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Usuario personalizado
AUTH_USER_MODEL = "usuarios.Usuario"

# === Middleware ===
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "cotizador_intranet.urls"

# === Templates ===
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.configuracion_sistema",
            ],
        },
    },
]

WSGI_APPLICATION = "cotizador_intranet.wsgi.application"

# === Base de Datos (PostgreSQL) ===
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "cotizador_db"),
        "USER": os.getenv("DB_USER", "postgres"),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", "127.0.0.1"),  # evita IPv6 con "localhost"
        "PORT": os.getenv("DB_PORT", "5432"),
        "CONN_MAX_AGE": 60,
    }
}

# === Password validators ===
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# === i18n / TZ ===
LANGUAGE_CODE = "es-cl"
TIME_ZONE = "America/Santiago"
USE_I18N = True
USE_TZ = True

# === Archivos estáticos / media ===
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]          # dev
STATIC_ROOT = BASE_DIR / "staticfiles"            # prod (collectstatic)

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# === Primary Key ===
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# === Login/Logout ===
LOGIN_REDIRECT_URL = "dashboard"
LOGIN_URL = "login"
LOGOUT_REDIRECT_URL = "login"

# === Email ===
# Para desarrollo: usa consola (no envía correos reales)
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend"
)
# Para producción, configura .env con:
# EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER or "no-reply@local")
