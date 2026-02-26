from django.urls import path
from .views import ProcesarLiveView

urlpatterns = [
    path('verificar-live/', ProcesarLiveView.as_view(), name='verificar_acceso'),
]