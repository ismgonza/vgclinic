# clinic_staff/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    StaffSpecialtyViewSet, StaffMemberViewSet,
    StaffLocationViewSet, AvailabilityScheduleViewSet
)

router = DefaultRouter()
router.register(r'specialties', StaffSpecialtyViewSet, basename='staffspecialty')
router.register(r'members', StaffMemberViewSet, basename='staffmember')
router.register(r'locations', StaffLocationViewSet, basename='stafflocation')
router.register(r'schedules', AvailabilityScheduleViewSet, basename='availabilityschedule')

urlpatterns = [
    path('', include(router.urls)),
]