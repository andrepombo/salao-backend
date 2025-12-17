from django.contrib import admin
from django.urls import path, include, re_path
from django.conf.urls.static import static
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from django.conf import settings
from drf_yasg import openapi
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import health_check
from .auth_views import demo_login

schema_view = get_schema_view(
    openapi.Info(
        title="Hair Salon API",
        default_version='v1',
        description="API para sistema de agendamento de salão de beleza. Este documento descreve os recursos disponíveis nesta API para gerenciar clientes, serviços, equipe e agendamentos.",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contato@salao.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health_check, name='health_check'),
    path('api/', include('apps.clients.urls')),
    path('api/', include('apps.services.urls')),
    path('api/', include('apps.team.urls')),
    path('api/', include('apps.appointments.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('demo-login/', demo_login, name='demo_login'),
    
    # Swagger/OpenAPI Documentation
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
