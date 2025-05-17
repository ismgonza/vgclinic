# clinic_catalog/signals.py
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import CatalogItem, Package

# You can add signals here as needed