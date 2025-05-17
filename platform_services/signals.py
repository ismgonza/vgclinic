# platform_services/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Feature, Service, Plan

# You can add signals here as needed