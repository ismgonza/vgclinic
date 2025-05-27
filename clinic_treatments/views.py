# clinic_treatments/views.py
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from platform_accounts.models import Account, AccountOwner, AccountUser
from platform_users.models import User
from .models import Treatment, TreatmentNote, TreatmentDetail, TreatmentScheduleHistory
from .serializers import (
    TreatmentSerializer, TreatmentCreateSerializer, TreatmentUpdateSerializer,
    TreatmentNoteSerializer, TreatmentDetailSerializer, TreatmentScheduleHistorySerializer
)

class TreatmentViewSet(viewsets.ModelViewSet):
    queryset = Treatment.objects.all()
    serializer_class = TreatmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'specialty', 'doctor', 'patient', 'scheduled_date', 'location']
    search_fields = ['patient__first_name', 'patient__last_name1', 'patient__id_number', 'catalog_item__name', 'notes']
    ordering_fields = ['scheduled_date', 'completed_date', 'status']
    
    def get_queryset(self):
        # Get account context
        account = self.get_account_context()

        # Start with base queryset
        queryset = Treatment.objects.all()
        
        # Filter by account if we have one
        if account:
            # Filter treatments by specialty's account (since treatments are linked to catalog items, which are linked to specialties, which are linked to accounts)
            queryset = queryset.filter(specialty__account=account)
        else:
            print("DEBUG: No account context - showing all treatments")
        
        # Apply date range filter if provided
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        if start_date and end_date:
            queryset = queryset.filter(scheduled_date__range=[start_date, end_date])
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TreatmentCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return TreatmentUpdateSerializer
        return TreatmentSerializer
    
    def get_account_context(self):
        """Get and validate account context from request header"""
        account_id = self.request.headers.get('X-Account-Context')
        
        if not account_id:
            return None
            
        try:
            account = Account.objects.get(account_id=account_id)
            
            # Check if user has access (unless they're staff/superuser)
            if self.request.user.is_staff or self.request.user.is_superuser:
                return account
            else:
                # Check if user is an owner of this account
                if AccountOwner.objects.filter(
                    user=self.request.user,
                    account=account,
                    is_active=True
                ).exists():
                    return account
                
                # Check if user is a member of this account
                if AccountUser.objects.filter(
                    user=self.request.user,
                    account=account,
                    is_active_in_account=True
                ).exists():
                    return account
                    
            return None
        except Account.DoesNotExist:
            return None
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
        
    def update(self, request, *args, **kwargs):
        # Get the treatment instance
        instance = self.get_object()        
        # Get the serializer
        serializer = self.get_serializer(instance, data=request.data, partial=True)        
        if serializer.is_valid():
            self.perform_update(serializer)
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    @action(detail=False, methods=['get'])
    def user_role_info(self, request):
        """Get current user's role information in the selected account"""
        try:
            account = self.get_account_context()
            
            if not account:
                return Response({'error': 'No account context'}, status=400)
            
            # Check if user is a doctor in this account
            user_is_doctor = AccountUser.objects.filter(
                user=request.user,
                account=account,
                role='doc',
                is_active_in_account=True
            ).exists()
            
            # Check if user is an owner (owners can act as doctors)
            user_is_owner = AccountOwner.objects.filter(
                user=request.user,
                account=account,
                is_active=True
            ).exists()
            
            # Get user's roles in this account
            user_roles = list(AccountUser.objects.filter(
                user=request.user,
                account=account,
                is_active_in_account=True
            ).values_list('role', flat=True))
            
            if user_is_owner:
                user_roles.append('owner')
            
            return Response({
                'is_doctor': user_is_doctor or user_is_owner,
                'is_owner': user_is_owner,
                'roles': user_roles,
                'user_id': request.user.id
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=500)

    @action(detail=False, methods=['get'])
    def form_options(self, request):
        """Get all options needed for treatment forms"""
        try:
            # Get account context
            account = self.get_account_context()
            
            # Get specialty filter parameter
            specialty_id = request.query_params.get('specialty_id', None)
            
            if account:
                if specialty_id:
                    # When specialty is specified, get doctors who practice that specialty
                    doctors = User.objects.filter(
                        account_memberships__account=account,
                        account_memberships__role='doc',
                        account_memberships__specialty_id=specialty_id,
                        account_memberships__is_active_in_account=True,
                        is_active=True
                    ).distinct()
                    
                    # Get owners who ALSO have doctor role for this specialty
                    specialty_qualified_owners = User.objects.filter(
                        owned_accounts__account=account,
                        owned_accounts__is_active=True,
                        account_memberships__account=account,
                        account_memberships__role='doc',
                        account_memberships__specialty_id=specialty_id,
                        account_memberships__is_active_in_account=True,
                        is_active=True
                    ).distinct()
                    
                    # Combine specialty doctors and specialty-qualified owners
                    all_doctors = doctors.union(specialty_qualified_owners).order_by('first_name', 'last_name')
                else:
                    # No specialty filter - get all doctors
                    doctors = User.objects.filter(
                        account_memberships__account=account,
                        account_memberships__role='doc',
                        account_memberships__is_active_in_account=True,
                        is_active=True
                    ).distinct()
                    
                    # Get all owners (since no specialty restriction)
                    owners = User.objects.filter(
                        owned_accounts__account=account,
                        owned_accounts__is_active=True,
                        is_active=True
                    ).distinct()
                    
                    # Combine doctors and owners
                    all_doctors = doctors.union(owners).order_by('first_name', 'last_name')
                                
            else:
                # Fallback: Get doctors from all accounts the user has access to
                # Get accounts where user is owner
                owned_accounts = AccountOwner.objects.filter(
                    user=request.user,
                    is_active=True
                ).values_list('account', flat=True)
                
                # Get accounts where user is member
                member_accounts = AccountUser.objects.filter(
                    user=request.user,
                    is_active_in_account=True
                ).values_list('account', flat=True)
                
                # Combine both account lists
                user_accounts = list(owned_accounts) + list(member_accounts)
                
                if specialty_id:
                    # Filter by specialty when specified
                    doctors = User.objects.filter(
                        account_memberships__account__in=user_accounts,
                        account_memberships__role='doc',
                        account_memberships__specialty_id=specialty_id,
                        account_memberships__is_active_in_account=True,
                        is_active=True
                    ).distinct()
                    
                    # Get owners who also have doctor role for this specialty
                    specialty_qualified_owners = User.objects.filter(
                        owned_accounts__account__in=user_accounts,
                        owned_accounts__is_active=True,
                        account_memberships__account__in=user_accounts,
                        account_memberships__role='doc',
                        account_memberships__specialty_id=specialty_id,
                        account_memberships__is_active_in_account=True,
                        is_active=True
                    ).distinct()
                    
                    # Combine specialty doctors and specialty-qualified owners
                    all_doctors = doctors.union(specialty_qualified_owners).order_by('first_name', 'last_name')
                else:
                    # No specialty filter - get all doctors
                    doctors = User.objects.filter(
                        account_memberships__account__in=user_accounts,
                        account_memberships__role='doc',
                        account_memberships__is_active_in_account=True,
                        is_active=True
                    ).distinct()
                    
                    # Get all owners (since no specialty restriction)
                    owners = User.objects.filter(
                        owned_accounts__account__in=user_accounts,
                        owned_accounts__is_active=True,
                        is_active=True
                    ).distinct()
                    
                    # Combine doctors and owners
                    all_doctors = doctors.union(owners).order_by('first_name', 'last_name')
            
            # Serialize the data
            from platform_users.serializers import UserSerializer
            doctors_data = UserSerializer(all_doctors, many=True).data
            
            return Response({
                'doctors': doctors_data
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=500)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        treatment = self.get_object()
        treatment.complete()
        serializer = self.get_serializer(treatment)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        treatment = self.get_object()
        treatment.cancel()
        serializer = self.get_serializer(treatment)
        return Response(serializer.data)
    

    @action(detail=True, methods=['post'])
    def add_note(self, request, pk=None):
        treatment = self.get_object()
        
        # Add the treatment ID to the request data before validation
        note_data = request.data.copy()
        note_data['treatment'] = treatment.id
        
        # Handle doctor assignment for medical notes
        if note_data.get('type') == 'MEDICAL':
            # Check if current user is a doctor in this account
            account = self.get_account_context()
            user_is_doctor = False
            
            if account:
                # Check if user is a doctor in this account
                user_is_doctor = AccountUser.objects.filter(
                    user=request.user,
                    account=account,
                    role='doc',
                    is_active_in_account=True
                ).exists()
                
                # Also check if user is an owner (owners can act as doctors)
                user_is_owner = AccountOwner.objects.filter(
                    user=request.user,
                    account=account,
                    is_active=True
                ).exists()
                
                user_is_doctor = user_is_doctor or user_is_owner
            
            if user_is_doctor:
                # Auto-assign to current user (doctor)
                note_data['assigned_doctor'] = request.user.id
            else:
                # Non-doctor must specify assigned doctor
                if not note_data.get('assigned_doctor'):
                    return Response(
                        {'assigned_doctor': ['This field is required for medical notes when you are not a doctor.']}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
        
        serializer = TreatmentNoteSerializer(data=note_data)
        
        if serializer.is_valid():
            note = serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TreatmentNoteViewSet(viewsets.ModelViewSet):
    queryset = TreatmentNote.objects.all()
    serializer_class = TreatmentNoteSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['treatment']
    ordering_fields = ['date']
    
    def get_queryset(self):
        """Filter notes by account context"""
        # Get account context
        account = self.get_account_context()

        # Start with base queryset
        queryset = TreatmentNote.objects.all()
        
        # Filter by account if we have one
        if account:
            # Filter treatment notes by the treatment's specialty's account
            queryset = queryset.filter(treatment__specialty__account=account)
        else:
            print("DEBUG: TreatmentNote - No account context - showing all notes")
        
        return queryset
    
    def get_account_context(self):
        """Get and validate account context from request header"""
        account_id = self.request.headers.get('X-Account-Context')
        
        if not account_id:
            return None
            
        try:
            account = Account.objects.get(account_id=account_id)
            
            # Check if user has access (unless they're staff/superuser)
            if self.request.user.is_staff or self.request.user.is_superuser:
                return account
            else:
                # Check if user is an owner of this account
                if AccountOwner.objects.filter(
                    user=self.request.user,
                    account=account,
                    is_active=True
                ).exists():
                    return account
                
                # Check if user is a member of this account
                if AccountUser.objects.filter(
                    user=self.request.user,
                    account=account,
                    is_active_in_account=True
                ).exists():
                    return account
                    
            return None
        except Account.DoesNotExist:
            return None
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class TreatmentDetailViewSet(viewsets.ModelViewSet):
    queryset = TreatmentDetail.objects.all()
    serializer_class = TreatmentDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['treatment', 'field_name']
    
    def get_queryset(self):
        """Filter treatment details by account context"""
        # Get account context
        account = self.get_account_context()

        # Start with base queryset
        queryset = TreatmentDetail.objects.all()
        
        # Filter by account if we have one
        if account:
            # Filter treatment details by the treatment's specialty's account
            queryset = queryset.filter(treatment__specialty__account=account)
        else:
            print("DEBUG: TreatmentDetail - No account context - showing all details")
        
        return queryset
    
    def get_account_context(self):
        """Get and validate account context from request header"""
        account_id = self.request.headers.get('X-Account-Context')
        
        if not account_id:
            return None
            
        try:
            account = Account.objects.get(account_id=account_id)
            
            # Check if user has access (unless they're staff/superuser)
            if self.request.user.is_staff or self.request.user.is_superuser:
                return account
            else:
                # Check if user is an owner of this account
                if AccountOwner.objects.filter(
                    user=self.request.user,
                    account=account,
                    is_active=True
                ).exists():
                    return account
                
                # Check if user is a member of this account
                if AccountUser.objects.filter(
                    user=self.request.user,
                    account=account,
                    is_active_in_account=True
                ).exists():
                    return account
                    
            return None
        except Account.DoesNotExist:
            return None