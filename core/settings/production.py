import os
from core.settings.base import *
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(Path.joinpath(BASE_DIR, '.env/env_prod'))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

SECRET_KEY = os.getenv('SECRET_KEY')

DEBUG = False

SECURE_SSL_REDIRECT = False  # Nginx is handling the redirect
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_DOMAIN = '.vgclinic.com'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
ALLOWED_HOSTS = ['vgclinic.com', 'portal.vgclinic.com', 'www.vgclinic.com']
CSRF_TRUSTED_ORIGINS = ['https://vgclinic.com', 'https://portal.vgclinic.com', 'https://www.vgclinic.com']

# SECURE_HSTS_SECONDS = 31536000  # 1 year
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True
# USE_X_FORWARDED_HOST = True

FRONTEND_URL = os.getenv('FRONTEND_URL', 'https://portal.vgclinic.com')


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.getenv('DB_NAME', default=''),
        'USER': os.getenv('DB_USER', default=''),
        'PASSWORD': os.getenv('DB_PASSWORD', default=''),
        'HOST': os.getenv('DB_HOST', default=''),
        'PORT': os.getenv('DB_PORT', default=''),
        'CONN_MAX_AGE': 600,  # connection persistence for 10 minutes
        # 'OPTIONS': {
        #     'connect_timeout': 5,
        # }
    }
}

STATIC_ROOT = '/app/staticfiles'
STATICFILES_DIRS = [
    Path.joinpath(BASE_DIR, 'static'),
]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# CHECK FOR STORAGE
# https://docs.djangoproject.com/en/5.0/ref/settings/#std-setting-STORAGES

# =================================================================
# Email settings for production - SMTP
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')  # or your SMTP server
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'False').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')  # your email
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')  # your app password
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@vgclinic.com')
EMAIL_SUBJECT_PREFIX = '[VGClinic] '

# Optional: Email timeout settings
EMAIL_TIMEOUT = 30