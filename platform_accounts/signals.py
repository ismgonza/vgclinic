# platform_accounts/signals.py
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Account, AccountUser

# You can add signals here as needed