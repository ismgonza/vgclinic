import os
from core.settings.base import *
from dotenv import load_dotenv
# from config.logging import *

# Load environment variables from .env file
load_dotenv(Path.joinpath(BASE_DIR, '.env/env_devel'))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# CORS settings - ONLY during development
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',
    }
}

STATIC_ROOT = Path.joinpath(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    Path.joinpath(BASE_DIR, 'static'),
]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
