# core/api.py
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Schema view for API documentation
schema_view = get_schema_view(
    openapi.Info(
        title="VGClinic API",
        default_version='v1',
        description="API for VGClinic - A modern clinic management system",
        terms_of_service="https://www.vgclinic.com/terms/",
        contact=openapi.Contact(email="contact@vgclinic.com"),
        license=openapi.License(name="Proprietary"),
    ),
    public=False,
    permission_classes=(permissions.IsAuthenticated,),
)