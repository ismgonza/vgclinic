# Update your platform_accounts/services.py

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils.translation import gettext as _
import logging

logger = logging.getLogger(__name__)

class InvitationEmailService:
    """Service for sending invitation emails."""
    
    @staticmethod
    def send_invitation_email(invitation):
        """
        Send an invitation email to the invited user.
        
        Args:
            invitation: AccountInvitation instance
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            # Check if user already exists
            from platform_users.models import User
            user_exists = User.objects.filter(email=invitation.email).exists()
            
            # Get language from account (default to Spanish)
            language = invitation.account.default_language
            
            # Prepare context for email template
            context = {
                'invitation': invitation,
                'account_name': invitation.account.account_name,
                'role_display': invitation.get_role_display(),
                'specialty_name': invitation.specialty.name if invitation.specialty else None,
                'invited_by_name': f"{invitation.invited_by.first_name} {invitation.invited_by.last_name}",
                'invited_by_email': invitation.invited_by.email,
                'acceptance_url': invitation.get_acceptance_url(),
                'user_exists': user_exists,
                'expires_at': invitation.expires_at,
                'personal_message': invitation.personal_message,
            }
            
            # Choose template based on whether user exists and language
            if user_exists:
                template_base = f'emails/{language}/invitation_existing_user'
                subject_key = 'existing_user'
            else:
                template_base = f'emails/{language}/invitation_new_user'
                subject_key = 'new_user'
            
            # Generate email content
            html_message = render_to_string(f'{template_base}.html', context)
            plain_message = render_to_string(f'{template_base}.txt', context)
            
            # Create subject line based on language
            if language == 'es':
                subjects = {
                    'existing_user': f"Te invitamos a unirte a {invitation.account.account_name}",
                    'new_user': f"Te invitamos a crear una cuenta con {invitation.account.account_name}"
                }
            else:  # English fallback
                subjects = {
                    'existing_user': f"You're invited to join {invitation.account.account_name}",
                    'new_user': f"You're invited to create an account with {invitation.account.account_name}"
                }
            
            subject = subjects[subject_key]
            
            # Send email
            success = send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[invitation.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            if success:
                logger.info(f"Invitation email sent successfully to {invitation.email} in {language}")
                return True
            else:
                logger.error(f"Failed to send invitation email to {invitation.email}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending invitation email to {invitation.email}: {str(e)}")
            return False
    
    @staticmethod
    def send_welcome_email(user, account):
        """
        Send a welcome email after invitation is accepted.
        
        Args:
            user: User instance
            account: Account instance
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            # Get language from account
            language = account.default_language
            
            context = {
                'user': user,
                'account': account,
                'login_url': f"{settings.FRONTEND_URL}/login",
            }
            
            template_base = f'emails/{language}/welcome'
            html_message = render_to_string(f'{template_base}.html', context)
            plain_message = render_to_string(f'{template_base}.txt', context)
            
            # Subject based on language
            if language == 'es':
                subject = f"¡Bienvenido a {account.account_name}!"
            else:
                subject = f"Welcome to {account.account_name}!"
            
            success = send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            if success:
                logger.info(f"Welcome email sent successfully to {user.email} in {language}")
                return True
            else:
                logger.error(f"Failed to send welcome email to {user.email}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending welcome email to {user.email}: {str(e)}")
            return False