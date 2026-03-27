from django.urls import path
from .views import (
    video_stream_view,
    CamaraListCreateView,
    CamaraDetailView,
    detectar_camaras_fisicas,
    capture_frame,
    reset_camera_service,
    camera_status,
)

urlpatterns = [
    # CRUD
    path('', CamaraListCreateView.as_view(), name='camara-list'),
    path('<int:pk>/', CamaraDetailView.as_view(), name='camara-detail'),

    # Hardware
    path('detectar/', detectar_camaras_fisicas, name='detectar'),

    # Gestión del servicio
    path('reset-service/', reset_camera_service, name='reset-service'),
    path('status/', camera_status, name='camera-status'),  # ← nuevo

    # Streaming y captura
    path('stream/<int:cam_idx>/', video_stream_view, name='video_stream'),
    path('capture/<int:hw_idx>/', capture_frame, name='capture_frame'),
]