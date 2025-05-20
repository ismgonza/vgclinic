# clinic_patients/serializers.py
from rest_framework import serializers
from django.apps import apps
from .models import Patient, PatientPhone, EmergencyContact, PatientAccount, MedicalHistory

# Import the Account model from platform_accounts app
Account = apps.get_model('platform_accounts', 'Account')

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

class PatientAccountSerializer(serializers.ModelSerializer):
    medical_histories = MedicalHistorySerializer(many=True, read_only=True)
    
    class Meta:
        model = PatientAccount
        fields = '__all__'

class PatientSerializer(serializers.ModelSerializer):
    phones = PatientPhoneSerializer(many=True, read_only=True)
    emergency_contacts = EmergencyContactSerializer(many=True, read_only=True)
    clinic_memberships = PatientAccountSerializer(many=True, read_only=True)
    
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
    account = serializers.PrimaryKeyRelatedField(write_only=True, required=True, 
                                               queryset=Account.objects.all())
    referral_source = serializers.CharField(required=False, write_only=True)
    consultation_reason = serializers.CharField(required=False, write_only=True)
    receive_notifications = serializers.BooleanField(default=False, write_only=True)
    
    class Meta:
        model = Patient
        exclude = ('created_at', 'updated_at')
    
    def create(self, validated_data):
        phones_data = validated_data.pop('phones', [])
        emergency_contacts_data = validated_data.pop('emergency_contacts', [])
        account = validated_data.pop('account')
        
        # Extract clinic-specific fields
        clinic_fields = {
            'referral_source': validated_data.pop('referral_source', ''),
            'consultation_reason': validated_data.pop('consultation_reason', ''),
            'receive_notifications': validated_data.pop('receive_notifications', False)
        }
        
        # Create the patient
        patient = Patient.objects.create(**validated_data)
        
        # Add phones
        for phone_data in phones_data:
            PatientPhone.objects.create(patient=patient, **phone_data)
        
        # Add emergency contacts
        for contact_data in emergency_contacts_data:
            EmergencyContact.objects.create(patient=patient, **contact_data)
        
        # Create the clinic association
        PatientAccount.objects.create(
            patient=patient,
            account=account,
            **clinic_fields
        )
        
        return patient