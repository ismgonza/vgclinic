# clinic_treatments/serializers.py
from rest_framework import serializers
from .models import Treatment, TreatmentNote, TreatmentDetail
from clinic_patients.serializers import PatientSerializer
from clinic_catalog.serializers import CatalogItemSerializer, SpecialtySerializer
from platform_users.serializers import UserSerializer
from clinic_locations.serializers import BranchSerializer


class TreatmentDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = TreatmentDetail
        fields = ('id', 'treatment', 'field_name', 'field_value')

class TreatmentNoteSerializer(serializers.ModelSerializer):
    created_by_details = UserSerializer(source='created_by', read_only=True)
    
    class Meta:
        model = TreatmentNote
        fields = ('id', 'treatment', 'date', 'note', 'created_by', 'created_by_details')
        read_only_fields = ('created_by',)

class TreatmentSerializer(serializers.ModelSerializer):
    patient_details = PatientSerializer(source='patient', read_only=True)
    catalog_item_details = CatalogItemSerializer(source='catalog_item', read_only=True)
    specialty_details = SpecialtySerializer(source='specialty', read_only=True)
    doctor_details = UserSerializer(source='doctor', read_only=True)
    created_by_details = UserSerializer(source='created_by', read_only=True)
    location_details = BranchSerializer(source='location', read_only=True)
    details = TreatmentDetailSerializer(many=True, read_only=True)
    additional_notes = TreatmentNoteSerializer(many=True, read_only=True)
    
    class Meta:
        model = Treatment
        fields = ('id', 'catalog_item', 'specialty', 'patient', 'notes', 
                  'scheduled_date', 'completed_date', 'status', 'doctor', 
                  'location', 'parent_treatment', 'phase_number', 'created_at', 
                  'updated_at', 'created_by', 'patient_details', 'catalog_item_details', 
                  'specialty_details', 'doctor_details', 'created_by_details',
                  'location_details', 'details', 'additional_notes')
        read_only_fields = ('created_at', 'updated_at', 'created_by')

class TreatmentCreateSerializer(serializers.ModelSerializer):
    details = TreatmentDetailSerializer(many=True, required=False)
    
    class Meta:
        model = Treatment
        fields = ('id', 'catalog_item', 'specialty', 'patient', 'notes', 
                  'scheduled_date', 'completed_date', 'status', 'doctor', 
                  'location', 'parent_treatment', 'phase_number', 'details')
    
    def create(self, validated_data):
        details_data = validated_data.pop('details', [])
        
        # Add the created_by field
        validated_data['created_by'] = self.context['request'].user
        
        treatment = Treatment.objects.create(**validated_data)
        
        for detail_data in details_data:
            TreatmentDetail.objects.create(treatment=treatment, **detail_data)
            
        return treatment