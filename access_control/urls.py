from django.urls import path

from .views import (
    ProcesarLiveView,
    RegistrarEmpleadoView
)

urlpatterns = [

    # Registro biométrico
    path(
        "registrar-empleado/",
        RegistrarEmpleadoView.as_view(),
        name="registrar_empleado"
    ),

    # Acceso biométrico
    path(
        "verificar-live/",
        ProcesarLiveView.as_view(),
        name="verificar_acceso"
    ),
]