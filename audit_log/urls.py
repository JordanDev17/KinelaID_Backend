from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AreaViewSet, RegistroAccesoViewSet, PermisoAreaViewSet

router = DefaultRouter()
router.register(r'areas', AreaViewSet)
router.register(r'registros', RegistroAccesoViewSet)
router.register(r'permisosarea', PermisoAreaViewSet)

urlpatterns = [
    path('', include(router.urls)),
]