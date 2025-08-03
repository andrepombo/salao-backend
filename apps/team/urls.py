from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TeamViewSet

router = DefaultRouter()
router.register(r'team', TeamViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
