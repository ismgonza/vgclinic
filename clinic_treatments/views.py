# clinic_treatments/views.py - UPDATED with consistent permission checks
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from platform_accounts.models import Account, AccountOwner, AccountUser
from platform_users.models import User
from core.permissions import AccountPermissionMixin
from .models import Treatment, TreatmentNote, TreatmentDetail, TreatmentScheduleHistory
from .serializers import (
    TreatmentSerializer, TreatmentCreateSerializer, TreatmentUpdateSerializer,
    TreatmentNoteSerializer, TreatmentDetailSerializer, TreatmentScheduleHistorySerializer
)

class TreatmentViewSet(AccountPermissionMixin, viewsets.ModelViewSet):
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
        if not account:
            return Treatment.objects.none()

        # Check permissions
        if not self.has_treatment_view_permission(account):
            return Treatment.objects.none()

        # Start with base queryset filtered by account
        queryset = Treatment.objects.filter(
            specialty__account=account
        ).select_related(
            'patient', 'catalog_item', 'specialty', 'doctor', 'created_by', 'location'
        )

        # Apply permission-based filtering
        queryset = self.apply_treatment_permissions_filter(queryset, account)
        
        # Apply date range filter if provided
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        if start_date and end_date:
            queryset = queryset.filter(scheduled_date__range=[start_date, end_date])
        
        return queryset
    
    def has_treatment_view_permission(self, account):
        """Check if user has any treatment view permission."""
        return self.check_permission('view_treatments_list', account) or \
               self.check_permission('view_treatments_assigned', account)
    
    def apply_treatment_permissions_filter(self, queryset, account):
        """Apply permission-based filtering to treatment queryset."""
        
        # If user can view all treatments, return full queryset
        if self.check_permission('view_treatments_list', account):
            return queryset
        
        # If user can only view assigned treatments
        if self.check_permission('view_treatments_assigned', account):
            return queryset.filter(doctor=self.request.user)
        
        # No view permissions
        return queryset.none()
    
    def retrieve(self, request, *args, **kwargs):
        """Override retrieve to check detail permissions."""
        account = self.get_account_context()
        if not account:
            return Response({'error': 'Account context required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user has detail view permission
        if not self.check_permission('view_treatments_detail', account):
            return Response(
                {'error': 'Permission denied. You do not have permission to view treatment details.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        treatment = self.get_object()
        
        # Additional check for assigned-only users
        if (self.check_permission('view_treatments_assigned', account) and 
            not self.check_permission('view_treatments_list', account)):
            if treatment.doctor != request.user:
                return Response(
                    {'error': 'Permission denied. You can only view treatments assigned to you.'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        
        return super().retrieve(request, *args, **kwargs)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TreatmentCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return TreatmentUpdateSerializer
        return TreatmentSerializer
    
    def create(self, request, *args, **kwargs):
        """Override create to check permissions."""
        account = self.get_account_context()
        if not account:
            return Response({'error': 'Account context required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check create permission
        if not self.check_permission('create_treatments', account):
            return Response(
                {'error': 'Permission denied. You do not have permission to create treatments.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """Override update to check permissions."""
        account = self.get_account_context()
        if not account:
            return Response({'error': 'Account context required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check edit permission
        if not self.check_permission('edit_treatments', account):
            return Response(
                {'error': 'Permission denied. You do not have permission to edit treatments.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        treatment = self.get_object()
        
        # Additional check for assigned-only users
        if (self.check_permission('view_treatments_assigned', account) and 
            not self.check_permission('view_treatments_list', account)):
            if treatment.doctor != request.user:
                return Response(
                    {'error': 'Permission denied. You can only edit treatments assigned to you.'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Get the serializer
        serializer = self.get_serializer(treatment, data=request.data, partial=True)        
        if serializer.is_valid():
            self.perform_update(serializer)
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
        
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
        """Mark treatment as completed."""
        account = self.get_account_context()
        if not account:
            return Response({'error': 'Account context required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check edit permission
        if not self.check_permission('edit_treatments', account):
            return Response(
                {'error': 'Permission denied. You do not have permission to modify treatments.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        treatment = self.get_object()
        
        # Additional check for assigned-only users
        if (self.check_permission('view_treatments_assigned', account) and 
            not self.check_permission('view_treatments_list', account)):
            if treatment.doctor != request.user:
                return Response(
                    {'error': 'Permission denied. You can only modify treatments assigned to you.'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        
        treatment.complete()
        serializer = self.get_serializer(treatment)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel treatment."""
        account = self.get_account_context()
        if not account:
            return Response({'error': 'Account context required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check edit permission
        if not self.check_permission('edit_treatments', account):
            return Response(
                {'error': 'Permission denied. You do not have permission to modify treatments.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        treatment = self.get_object()
        
        # Additional check for assigned-only users
        if (self.check_permission('view_treatments_assigned', account) and 
            not self.check_permission('view_treatments_list', account)):
            if treatment.doctor != request.user:
                return Response(
                    {'error': 'Permission denied. You can only modify treatments assigned to you.'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        
        treatment.cancel()
        serializer = self.get_serializer(treatment)
        return Response(serializer.data)
    

    @action(detail=True, methods=['post'])
    def add_note(self, request, pk=None):
        """Add a note to treatment."""
        account = self.get_account_context()
        if not account:
            return Response({'error': 'Account context required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check create note permission
        if not self.check_permission('create_treatment_notes', account):
            return Response(
                {'error': 'Permission denied. You do not have permission to create treatment notes.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        treatment = self.get_object()
        
        # Additional check for assigned-only users
        if (self.check_permission('view_treatments_assigned', account) and 
            not self.check_permission('view_treatments_list', account)):
            if treatment.doctor != request.user:
                return Response(
                    {'error': 'Permission denied. You can only add notes to treatments assigned to you.'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Add the treatment ID to the request data before validation
        note_data = request.data.copy()
        note_data['treatment'] = treatment.id
        
        # Handle doctor assignment for medical notes
        if note_data.get('type') == 'MEDICAL':
            # Check if current user is a doctor in this account
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

class TreatmentNoteViewSet(AccountPermissionMixin, viewsets.ModelViewSet):
    queryset = TreatmentNote.objects.all()
    serializer_class = TreatmentNoteSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['treatment']
    ordering_fields = ['date']
    
    def get_queryset(self):
        """Filter notes by account context and permissions."""
        account = self.get_account_context()
        if not account:
            return TreatmentNote.objects.none()

        # Check if user has permission to view treatment notes
        if not (self.check_permission('view_treatment_notes_list', account) or 
                self.check_permission('view_treatments_assigned', account)):
            return TreatmentNote.objects.none()

        # Start with base queryset filtered by account
        queryset = TreatmentNote.objects.filter(
            treatment__specialty__account=account
        ).select_related('treatment', 'created_by', 'assigned_doctor')
        
        # Apply permission-based filtering
        if (self.check_permission('view_treatments_assigned', account) and 
            not self.check_permission('view_treatment_notes_list', account)):
            # User can only see notes from treatments assigned to them
            queryset = queryset.filter(treatment__doctor=self.request.user)
        
        return queryset
    
    def retrieve(self, request, *args, **kwargs):
        """Override retrieve to check detail permissions."""
        account = self.get_account_context()
        if not account:
            return Response({'error': 'Account context required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check detail permission
        if not self.check_permission('view_treatment_notes_detail', account):
            return Response(
                {'error': 'Permission denied. You do not have permission to view treatment note details.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().retrieve(request, *args, **kwargs)
    
    def create(self, request, *args, **kwargs):
        """Override create to check permissions."""
        account = self.get_account_context()
        if not account:
            return Response({'error': 'Account context required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check create permission
        if not self.check_permission('create_treatment_notes', account):
            return Response(
                {'error': 'Permission denied. You do not have permission to create treatment notes.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """Override update to check permissions."""
        account = self.get_account_context()
        if not account:
            return Response({'error': 'Account context required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check edit permission
        if not self.check_permission('edit_treatment_notes', account):
            return Response(
                {'error': 'Permission denied. You do not have permission to edit treatment notes.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class TreatmentDetailViewSet(AccountPermissionMixin, viewsets.ModelViewSet):
    queryset = TreatmentDetail.objects.all()
    serializer_class = TreatmentDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['treatment', 'field_name']
    
    def get_queryset(self):
        """Filter treatment details by account context and permissions."""
        account = self.get_account_context()
        if not account:
            return TreatmentDetail.objects.none()

        # Check if user has permission to view treatment history
        if not (self.check_permission('view_treatment_history_list', account) or 
                self.check_permission('view_treatments_assigned', account)):
            return TreatmentDetail.objects.none()

        # Start with base queryset filtered by account
        queryset = TreatmentDetail.objects.filter(
            treatment__specialty__account=account
        ).select_related('treatment')
        
        # Apply permission-based filtering
        if (self.check_permission('view_treatments_assigned', account) and 
            not self.check_permission('view_treatment_history_list', account)):
            # User can only see details from treatments assigned to them
            queryset = queryset.filter(treatment__doctor=self.request.user)
        
        return queryset
    
    def retrieve(self, request, *args, **kwargs):
        """Override retrieve to check detail permissions."""
        account = self.get_account_context()
        if not account:
            return Response({'error': 'Account context required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check detail permission
        if not self.check_permission('view_treatment_history_detail', account):
            return Response(
                {'error': 'Permission denied. You do not have permission to view treatment history details.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().retrieve(request, *args, **kwargs)
    
    def create(self, request, *args, **kwargs):
        """Override create to check permissions."""
        account = self.get_account_context()
        if not account:
            return Response({'error': 'Account context required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check create permission
        if not self.check_permission('create_treatment_history', account):
            return Response(
                {'error': 'Permission denied. You do not have permission to create treatment history.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """Override update to check permissions."""
        account = self.get_account_context()
        if not account:
            return Response({'error': 'Account context required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check edit permission
        if not self.check_permission('edit_treatment_history', account):
            return Response(
                {'error': 'Permission denied. You do not have permission to edit treatment history.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)