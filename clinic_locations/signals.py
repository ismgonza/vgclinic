# clinic_locations/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Location
from platform_contracts.models import UsageQuota

@receiver(post_save, sender=Location)
def update_location_usage(sender, instance, created, **kwargs):
    """
    Update location usage quota when a new location is created.
    """
    if created:
        # Find active subscription for this account
        active_subscription = instance.account.subscriptions.filter(
            status__in=['active', 'trialing']
        ).first()
        
        if active_subscription:
            # Update location quota if it exists
            location_quota = active_subscription.quotas.filter(quota_type='locations').first()
            if location_quota:
                # Count current locations
                current_locations = Location.objects.filter(account=instance.account).count()
                
                # Update usage
                location_quota.current_usage = current_locations
                location_quota.save()

@receiver(post_delete, sender=Location)
def decrease_location_usage(sender, instance, **kwargs):
    """
    Decrease location usage quota when a location is deleted.
    """
    # Find active subscription for this account
    active_subscription = instance.account.subscriptions.filter(
        status__in=['active', 'trialing']
    ).first()
    
    if active_subscription:
        # Update location quota if it exists
        location_quota = active_subscription.quotas.filter(quota_type='locations').first()
        if location_quota:
            # Count current locations (already decreased by the deletion)
            current_locations = Location.objects.filter(account=instance.account).count()
            
            # Update usage
            location_quota.current_usage = current_locations
            location_quota.save()