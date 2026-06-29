SECRET_KEY = "reverse-vibe-coding-dev"
DEBUG = True

ROOT_URLCONF = "app.urls"
ALLOWED_HOSTS = ["*"]
INSTALLED_APPS = [
    "app"
]
MIDDLEWARE = []
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "db.sqlite3",
    }
}
