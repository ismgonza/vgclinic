# clinic_staff/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import StaffMember, StaffLocation
from platform_accounts.models import AccountUser
from platform_contracts.models import UsageQuota

@receiver(post_save, sender=StaffMember)
def update_user_quota(sender, instance, created, **kwargs):
    """
    Update user quota when a new staff member is created.
    """
    if created:
        # Find active subscription for this account
        account = instance.account_user.account
        active_subscription = account.subscriptions.filter(
            status__in=['active', 'trialing']
        ).first()
        
        if active_subscription:
            # Update user quota if it exists
            user_quota = active_subscription.quotas.filter(quota_type='users').first()
            if user_quota:
                # Count current staff members
                current_staff = StaffMember.objects.filter(
                    account_user__account=account
                ).count()
                
                # Update usage
                user_quota.current_usage = current_staff
                user_quota.save()

@receiver(post_delete, sender=StaffMember)
def decrease_user_quota(sender, instance, **kwargs):
    """
    Decrease user quota when a staff member is deleted.
    """
    # Find active subscription for this account
    account = instance.account_user.account
    active_subscription = account.subscriptions.filter(
        status__in=['active', 'trialing']
    ).first()
    
    if active_subscription:
        # Update user quota if it exists
        user_quota = active_subscription.quotas.filter(quota_type='users').first()
        if user_quota:
            # Count current staff members (already decreased by the deletion)
            current_staff = StaffMember.objects.filter(
                account_user__account=account
            ).count()
            
            # Update usage
            user_quota.current_usage = current_staff
            user_quota.save()