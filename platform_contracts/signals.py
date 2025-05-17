# platform_contracts/signals.py
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Subscription, Invoice, InvoiceItem

@receiver(pre_save, sender=Invoice)
def calculate_invoice_total(sender, instance, **kwargs):
    """
    Calculate the total amount of the invoice before saving.
    """
    instance.total_amount = instance.amount + instance.tax_amount