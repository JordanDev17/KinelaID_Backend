from django.urls import path
from .views import VideoStreamView, CamaraListCreateView, CamaraDetailView, detectar_camaras_fisicas, capture_frame

urlpatterns = [
    # Ruta para obtener la lista de cámaras (GET) y crear nuevas (POST)
    path('', CamaraListCreateView.as_view(), name='camara-list'),
    path('capture/<int:hw_idx>/', capture_frame),
    # Ruta para ver/editar/borrar una cámara específica
    path('<int:pk>/', CamaraDetailView.as_view(), name='camara-detail'),
    
    # EL ENDPOINT CRÍTICO: Aquí es donde Angular y Monitor.py verán el video
    # Ejemplo: http://127.0.0.1:8000/api/cameras/stream/0/
    path('stream/<int:cam_idx>/', VideoStreamView.as_view(), name='video-stream'),
    
    path('detectar/', detectar_camaras_fisicas, name='detectar'),
    
    
]