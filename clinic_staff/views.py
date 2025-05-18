from django.shortcuts import render
from rest_framework import viewsets, permissions, status, filters
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
import uuid
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth import get_user_model

from .models import StaffSpecialty, StaffMember, StaffLocation, AvailabilitySchedule
from .serializers import (
    StaffSpecialtySerializer, StaffMemberSerializer, StaffMemberListSerializer,
    StaffLocationSerializer, AvailabilityScheduleSerializer
)
from platform_accounts.permissions import IsAccountMember
from platform_accounts.models import AccountUser

User = get_user_model()

class StaffSpecialtyViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows staff specialties to be viewed or edited.
    """
    serializer_class = StaffSpecialtySerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    
    def get_queryset(self):
        """
        Filter specialties based on the current user's permissions.
        """
        user = self.request.user
        account_id = self.request.query_params.get('account_id')
        
        if user.is_staff:
            queryset = StaffSpecialty.objects.all()
        else:
            # Only show specialties for accounts the user is a member of
            queryset = StaffSpecialty.objects.filter(
                account__members__user=user,
                account__members__is_active=True
            )
        
        if account_id:
            queryset = queryset.filter(account_id=account_id)
            
        return queryset.order_by('name')
    
class StaffMemberViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows staff members to be viewed or edited.
    """
    permission_classes = [permissions.IsAuthenticated, IsAccountMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'staff_role', 'can_book_appointments']
    search_fields = [
        'account_user__user__first_name', 
        'account_user__user__last_name',
        'account_user__user__email',
        'job_title'
    ]
    ordering_fields = [
        'account_user__user__first_name', 
        'account_user__user__last_name',
        'job_title',
        'created_at'
    ]
    
    def get_queryset(self):
        """
        Filter staff members based on the current user's permissions.
        """
        user = self.request.user
        account_id = self.request.query_params.get('account_id')
        location_id = self.request.query_params.get('location_id')
        specialty_id = self.request.query_params.get('specialty_id')
        
        if user.is_staff:
            queryset = StaffMember.objects.all()
        else:
            # Only show staff for accounts the user is a member of
            queryset = StaffMember.objects.filter(
                account_user__account__members__user=user,
                account_user__account__members__is_active=True
            )
        
        if account_id:
            queryset = queryset.filter(account_user__account_id=account_id)
            
        if location_id:
            queryset = queryset.filter(assigned_locations__id=location_id)
            
        if specialty_id:
            queryset = queryset.filter(specialties__id=specialty_id)
            
        return queryset.select_related('account_user__user', 'account_user__account').distinct()
    
    def get_serializer_class(self):
        """
        Return different serializers for list and detail actions.
        """
        if self.action == 'list':
            return StaffMemberListSerializer
        return StaffMemberSerializer
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Custom create method to handle creating or associating User, AccountUser, and StaffMember.
        Checks for existing users by email or ID number.
        """
        # Extract user data
        user_data = request.data.get('user_data', {})
        email = user_data.get('email')
        id_number = user_data.get('id_number')
        account_id = request.data.get('account')
        
        # Validate required fields
        if not all([email, account_id]):
            return Response(
                {'error': 'Email and account are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user exists by email or ID number
        existing_user = None
        if email:
            existing_user = User.objects.filter(email=email).first()
        
        if not existing_user and id_number:
            existing_user = User.objects.filter(id_number=id_number).first()
        
        if existing_user:
            # User exists, check if they have an AccountUser for this account
            account_user = AccountUser.objects.filter(
                user=existing_user,
                account_id=account_id
            ).first()
            
            if not account_user:
                # User exists but not in this account, create AccountUser
                account_user = AccountUser.objects.create(
                    user=existing_user,
                    account_id=account_id,
                    role='staff'
                )
            
            # Check if staff member already exists for this account_user
            existing_staff = StaffMember.objects.filter(account_user=account_user).first()
            
            if existing_staff:
                return Response(
                    {'error': 'This user is already a staff member in this account'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            # User doesn't exist, create new user
            first_name = user_data.get('first_name')
            last_name = user_data.get('last_name')
            password = user_data.get('password')
            
            if not all([first_name, last_name, password]):
                return Response(
                    {'error': 'First name, last name, and password are required for new users'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Create the user with ID number if provided
            user_create_data = {
                'email': email,
                'password': password,
                'first_name': first_name,
                'last_name': last_name,
            }
            
            if id_number:
                user_create_data['id_number'] = id_number
                
            existing_user = User.objects.create_user(**user_create_data)
            
            # Create the account user
            account_user = AccountUser.objects.create(
                user=existing_user,
                account_id=account_id,
                role='staff'  # Default role for staff members
            )
        
        # Prepare staff member data
        staff_data = request.data.copy()
        staff_data['account_user'] = account_user.id
        
        # Remove user fields that are now handled
        if 'user_data' in staff_data:
            del staff_data['user_data']
        if 'account' in staff_data:
            del staff_data['account']
        
        # Create the staff member
        serializer = self.get_serializer(data=staff_data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    @transaction.atomic
    def perform_create(self, serializer):
        staff_member = serializer.save()
        
        # Handle assigned locations
        locations = self.request.data.get('locations', [])
        if isinstance(locations, list):
            for location in locations:
                is_primary = location.get('is_primary', False)
                StaffLocation.objects.create(
                    staff=staff_member,
                    location_id=location.get('id'),
                    is_primary=is_primary
                )
        
        # Handle availability schedules
        schedules = self.request.data.get('schedules', [])
        if isinstance(schedules, list):
            for schedule in schedules:
                AvailabilitySchedule.objects.create(
                    staff=staff_member,
                    location_id=schedule.get('location_id'),
                    day_of_week=schedule.get('day_of_week'),
                    start_time=schedule.get('start_time'),
                    end_time=schedule.get('end_time'),
                    is_available=schedule.get('is_available', True)
                )
    
    @action(detail=True, methods=['get'])
    def schedules(self, request, pk=None):
        """
        Get the availability schedules for a staff member.
        """
        staff_member = self.get_object()
        schedules = staff_member.availability_schedules.all()
        serializer = AvailabilityScheduleSerializer(schedules, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def locations(self, request, pk=None):
        """
        Get the locations assigned to a staff member.
        """
        staff_member = self.get_object()
        locations = staff_member.location_assignments.all()
        serializer = StaffLocationSerializer(locations, many=True)
        return Response(serializer.data)
    
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        """
        Custom delete method that only removes the StaffMember record,
        but preserves the User and AccountUser records.
        """
        instance = self.get_object()
        
        # Perform regular delete
        self.perform_destroy(instance)
        
        return Response(status=status.HTTP_204_NO_CONTENT)

class StaffInvitationView(APIView):
    """
    API endpoint to invite new staff members via email.
    """
    permission_classes = [permissions.IsAuthenticated, IsAccountMember]
    
    def post(self, request):
        email = request.data.get('email')
        role = request.data.get('role')
        account_id = request.data.get('account')
        
        if not all([email, role, account_id]):
            return Response(
                {'error': 'Email, role, and account are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate a unique token for the invitation
        invitation_token = str(uuid.uuid4())
        expires_at = timezone.now() + timedelta(days=7)
        
        # Save the invitation
        invitation, created = StaffInvitation.objects.update_or_create(
            email=email,
            account_id=account_id,
            defaults={
                'role': role,
                'token': invitation_token,
                'expires_at': expires_at,
                'invited_by': request.user
            }
        )
        
        # Send invitation email
        invite_url = f"{settings.FRONTEND_URL}/staff/accept-invite/{invitation_token}"
        
        email_context = {
            'invite_url': invite_url,
            'account_name': invitation.account.name,
            'role': dict(StaffMember.ROLE_CHOICES).get(role, role),
            'expiry_date': expires_at.strftime('%Y-%m-%d')
        }
        
        email_html = render_to_string('emails/staff_invitation.html', email_context)
        email_text = render_to_string('emails/staff_invitation.txt', email_context)
        
        send_mail(
            subject=f"You've been invited to join {invitation.account.name}",
            message=email_text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=email_html,
            fail_silently=False
        )
        
        return Response({'status': 'invitation sent'})

class StaffLocationViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows staff location assignments to be viewed or edited.
    """
    serializer_class = StaffLocationSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountMember]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['is_primary', 'staff', 'location']
    ordering_fields = ['created_at']
    
    def get_queryset(self):
        """
        Filter staff locations based on the current user's permissions.
        """
        user = self.request.user
        staff_id = self.request.query_params.get('staff_id')
        location_id = self.request.query_params.get('location_id')
        
        if user.is_staff:
            queryset = StaffLocation.objects.all()
        else:
            # Only show staff locations for accounts the user is a member of
            queryset = StaffLocation.objects.filter(
                staff__account_user__account__members__user=user,
                staff__account_user__account__members__is_active=True
            )
        
        if staff_id:
            queryset = queryset.filter(staff_id=staff_id)
            
        if location_id:
            queryset = queryset.filter(location_id=location_id)
            
        return queryset.order_by('-is_primary', 'location__name')


class AvailabilityScheduleViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows staff availability schedules to be viewed or edited.
    """
    serializer_class = AvailabilityScheduleSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountMember]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['staff', 'location', 'day_of_week', 'is_available']
    ordering_fields = ['day_of_week', 'start_time']
    
    def get_queryset(self):
        """
        Filter availability schedules based on the current user's permissions.
        """
        user = self.request.user
        staff_id = self.request.query_params.get('staff_id')
        location_id = self.request.query_params.get('location_id')
        
        if user.is_staff:
            queryset = AvailabilitySchedule.objects.all()
        else:
            # Only show schedules for accounts the user is a member of
            queryset = AvailabilitySchedule.objects.filter(
                staff__account_user__account__members__user=user,
                staff__account_user__account__members__is_active=True
            )
        
        if staff_id:
            queryset = queryset.filter(staff_id=staff_id)
            
        if location_id:
            queryset = queryset.filter(location_id=location_id)
            
        return queryset.order_by('staff', 'location', 'day_of_week', 'start_time')