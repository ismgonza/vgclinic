# clinic_patients/views.py
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Patient, PatientPhone, EmergencyContact, MedicalHistory
from .serializers import (
    PatientSerializer, PatientCreateSerializer, PatientPhoneSerializer,
    EmergencyContactSerializer, MedicalHistorySerializer
)

class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['gender', 'marital_status', 'is_foreign', 'province', 'canton']
    search_fields = ['first_name', 'last_name1', 'last_name2', 'id_number', 'email']
    ordering_fields = ['admission_date', 'first_name', 'last_name1', 'birth_date']
    
    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update':
            return PatientCreateSerializer
        return PatientSerializer
    
    @action(detail=True, methods=['get'])
    def medical_history(self, request, pk=None):
        patient = self.get_object()
        histories = patient.medical_histories.all()
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

class MedicalHistoryViewSet(viewsets.ModelViewSet):
    queryset = MedicalHistory.objects.all()
    serializer_class = MedicalHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['patient', 'information_confirmed']