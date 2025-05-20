# clinic_patients/views.py
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Patient, PatientPhone, EmergencyContact, PatientAccount, MedicalHistory
from .serializers import (
    PatientSerializer, PatientCreateSerializer, PatientPhoneSerializer,
    EmergencyContactSerializer, PatientAccountSerializer, MedicalHistorySerializer
)

class PatientViewSet(viewsets.ModelViewSet):
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['gender', 'marital_status', 'is_foreign', 'province', 'canton']
    search_fields = ['first_name', 'last_name1', 'last_name2', 'id_number', 'email']
    ordering_fields = ['first_name', 'last_name1', 'birth_date']
    
    def get_queryset(self):
        # If using request.account, filter patients by the current account
        if hasattr(self.request, 'account'):
            return Patient.objects.filter(clinic_memberships__account=self.request.account).distinct()
        return Patient.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update':
            return PatientCreateSerializer
        return PatientSerializer
    
    @action(detail=True, methods=['get'])
    def medical_history(self, request, pk=None):
        patient = self.get_object()
        account = getattr(request, 'account', None)
        
        if account:
            # Get medical histories specific to this account
            try:
                patient_account = PatientAccount.objects.get(patient=patient, account=account)
                histories = patient_account.medical_histories.all()
                serializer = MedicalHistorySerializer(histories, many=True)
                return Response(serializer.data)
            except PatientAccount.DoesNotExist:
                return Response({"detail": "Patient not found in this clinic"}, status=404)
        else:
            # If no account context, return all histories (admin view)
            histories = MedicalHistory.objects.filter(
                patient_account__patient=patient
            )
            serializer = MedicalHistorySerializer(histories, many=True)
            return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_phone(self, request, pk=None):
        patient = self.get_object()
        serializer = PatientPhoneSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(patient=patient)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
    
    @action(detail=True, methods=['post'])
    def add_emergency_contact(self, request, pk=None):
        patient = self.get_object()
        serializer = EmergencyContactSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(patient=patient)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
    
    @action(detail=True, methods=['post'])
    def add_to_clinic(self, request, pk=None):
        patient = self.get_object()
        
        # Make sure account is provided
        if 'account' not in request.data:
            return Response({"detail": "Account ID is required"}, status=400)
        
        # Check if patient is already in this clinic
        if PatientAccount.objects.filter(patient=patient, account_id=request.data['account']).exists():
            return Response({"detail": "Patient already belongs to this clinic"}, status=400)
        
        serializer = PatientAccountSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(patient=patient)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

class PatientAccountViewSet(viewsets.ModelViewSet):
    serializer_class = PatientAccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if hasattr(self.request, 'account'):
            return PatientAccount.objects.filter(account=self.request.account)
        return PatientAccount.objects.all()
    
    @action(detail=True, methods=['post'])
    def add_medical_history(self, request, pk=None):
        patient_account = self.get_object()
        serializer = MedicalHistorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(patient_account=patient_account)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

class MedicalHistoryViewSet(viewsets.ModelViewSet):
    serializer_class = MedicalHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if hasattr(self.request, 'account'):
            return MedicalHistory.objects.filter(patient_account__account=self.request.account)
        return MedicalHistory.objects.all()