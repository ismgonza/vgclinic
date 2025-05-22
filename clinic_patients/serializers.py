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

    def update(self, instance, validated_data):
        """Custom update method to handle nested fields"""
        # Extract nested fields
        phones_data = validated_data.pop('phones', None)
        emergency_contacts_data = validated_data.pop('emergency_contacts', None)
        account_data = validated_data.pop('account', None)
        
        # Clinic-specific fields
        clinic_fields = {
            'referral_source': validated_data.pop('referral_source', None),
            'consultation_reason': validated_data.pop('consultation_reason', None),
            'receive_notifications': validated_data.pop('receive_notifications', None)
        }
        
        # Update the patient instance
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Handle phones - if provided, replace existing ones
        if phones_data is not None:
            # Delete existing phones
            instance.phones.all().delete()
            # Create new ones
            for phone_data in phones_data:
                PatientPhone.objects.create(patient=instance, **phone_data)
        
        # Handle emergency contacts - if provided, replace existing ones
        if emergency_contacts_data is not None:
            # Delete existing emergency contacts
            instance.emergency_contacts.all().delete()
            # Create new ones
            for contact_data in emergency_contacts_data:
                EmergencyContact.objects.create(patient=instance, **contact_data)
        
        # Handle clinic membership (account) if provided
        if account_data:
            # Try to get the existing clinic membership
            try:
                patient_account = PatientAccount.objects.get(patient=instance, account=account_data)
                # Update clinic-specific fields for existing membership
                for field, value in clinic_fields.items():
                    if value is not None:
                        setattr(patient_account, field, value)
                patient_account.save()
            except PatientAccount.DoesNotExist:
                # Create a new clinic membership
                clinic_fields_clean = {k: v for k, v in clinic_fields.items() if v is not None}
                PatientAccount.objects.create(
                    patient=instance, 
                    account=account_data,
                    **clinic_fields_clean
                )
        elif any(v is not None for v in clinic_fields.values()):
            # Update clinic-specific fields for existing memberships
            for patient_account in instance.clinic_memberships.all():
                for field, value in clinic_fields.items():
                    if value is not None:
                        setattr(patient_account, field, value)
                patient_account.save()
        
        return instance
    
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