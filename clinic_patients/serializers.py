# clinic_patients/serializers.py
from rest_framework import serializers
from .models import Patient, PatientPhone, EmergencyContact, MedicalHistory

class PatientPhoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientPhone
        fields = ('id', 'phone_number', 'phone_type')

class EmergencyContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyContact
        fields = ('id', 'first_name', 'last_name1', 'last_name2', 'phone', 'relationship')

class MedicalHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalHistory
        fields = '__all__'

class PatientSerializer(serializers.ModelSerializer):
    phones = PatientPhoneSerializer(many=True, read_only=True)
    emergency_contacts = EmergencyContactSerializer(many=True, read_only=True)
    medical_histories = MedicalHistorySerializer(many=True, read_only=True)
    
    class Meta:
        model = Patient
        fields = '__all__'
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['full_name'] = f"{instance.first_name} {instance.last_name1} {instance.last_name2}".strip()
        return representation

class PatientCreateSerializer(serializers.ModelSerializer):
    phones = PatientPhoneSerializer(many=True, required=False)
    emergency_contacts = EmergencyContactSerializer(many=True, required=False)
    
    class Meta:
        model = Patient
        fields = '__all__'
    
    def create(self, validated_data):
        phones_data = validated_data.pop('phones', [])
        emergency_contacts_data = validated_data.pop('emergency_contacts', [])
        
        patient = Patient.objects.create(**validated_data)
        
        for phone_data in phones_data:
            PatientPhone.objects.create(patient=patient, **phone_data)
            
        for contact_data in emergency_contacts_data:
            EmergencyContact.objects.create(patient=patient, **contact_data)
            
        return patient