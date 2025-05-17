# platform_services/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FeatureViewSet, ServiceViewSet, PlanViewSet

router = DefaultRouter()
router.register(r'features', FeatureViewSet)
router.register(r'services', ServiceViewSet)
router.register(r'plans', PlanViewSet, basename='plan')

urlpatterns = [
    path('', include(router.urls)),
]