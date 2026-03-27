import cv2
import time
import logging

from django.http import StreamingHttpResponse, HttpResponse
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import csrf_exempt

from .models import Camara
from .serializers import CamaraSerializer
from .camera_manager import camera_hub_instance

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# CRUD de Cámaras
# ------------------------------------------------------------------

class CamaraListCreateView(generics.ListCreateAPIView):
    queryset = Camara.objects.all()
    serializer_class = CamaraSerializer


class CamaraDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Camara.objects.all()
    serializer_class = CamaraSerializer


# ------------------------------------------------------------------
# Detección de hardware
# ------------------------------------------------------------------

@api_view(['GET'])
def detectar_camaras_fisicas(request):
    disponibles = []
    manager = camera_hub_instance
    for i in range(5):
        if manager.is_running(i):
            disponibles.append({"index": i, "label": f"Cámara Activa {i}", "running": True})
            continue
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            disponibles.append({"index": i, "label": f"Cámara USB {i}", "running": False})
            cap.release()
    return Response(disponibles)


# ------------------------------------------------------------------
# Reinicio del servicio
# ------------------------------------------------------------------

@api_view(['POST'])
def reset_camera_service(request):
    """
    Detiene todos los hilos, libera el hardware y reinicia las cámaras
    activas según la base de datos. Retorna el estado final.
    """
    manager = camera_hub_instance

    try:
        manager.reset_all()

        # Espera breve para que los hilos arranquen
        time.sleep(1.5)

        estado = manager.status()
        activas = [idx for idx, s in estado.items() if s["thread_alive"]]

        return Response({
            "status": "success",
            "message": f"Servicio reiniciado. Cámaras activas: {activas}",
            "cameras": estado,
        })

    except Exception as e:
        logger.exception("Error en reset_camera_service")
        return Response({"status": "error", "message": str(e)}, status=500)


@api_view(['GET'])
def camera_status(request):
    """Endpoint de salud: devuelve el estado de cada cámara en memoria."""
    return Response(camera_hub_instance.status())


# ------------------------------------------------------------------
# Streaming MJPEG
# ------------------------------------------------------------------

# Tiempo máximo sin frames antes de cerrar el stream (segundos).
# El frontend detectará el corte y puede reconectar.
STREAM_NO_FRAME_TIMEOUT = 15


def gen_shared_frames(hw_idx: int):
    """
    Generador MJPEG para la cámara `hw_idx`.

    Mejoras respecto a la versión anterior:
    - Intenta arrancar la cámara si no está corriendo.
    - No corta el stream ante frames momentáneamente nulos (espera
      hasta STREAM_NO_FRAME_TIMEOUT segundos antes de rendirse).
    - Limita el frame rate a ~30 fps para no saturar la red/CPU.
    """
    manager = camera_hub_instance

    # Si la cámara no está corriendo, intentar iniciarla
    if not manager.is_running(hw_idx):
        logger.info(f"Stream {hw_idx}: cámara no corriendo, intentando iniciar…")
        manager.start_camera(hw_idx)
        time.sleep(1.0)  # Espera a que el primer frame esté listo

    no_frame_since = None
    frame_interval = 1.0 / 30  # 30 fps máx

    while True:
        frame = manager.get_frame(hw_idx)

        if frame is None:
            # Registra cuándo empezó la sequía de frames
            if no_frame_since is None:
                no_frame_since = time.time()
            elif time.time() - no_frame_since > STREAM_NO_FRAME_TIMEOUT:
                logger.warning(
                    f"Stream {hw_idx}: sin frames por {STREAM_NO_FRAME_TIMEOUT} s. "
                    "Cerrando stream para que el cliente reconecte."
                )
                break
            time.sleep(0.05)
            continue

        # Frames llegando con normalidad
        no_frame_since = None

        ret, buffer = cv2.imencode(
            ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70]
        )
        if not ret:
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + buffer.tobytes()
            + b"\r\n"
        )

        time.sleep(frame_interval)


@csrf_exempt
@xframe_options_exempt
def video_stream_view(request, cam_idx: int):
    idx = int(cam_idx)
    response = StreamingHttpResponse(
        gen_shared_frames(idx),
        content_type="multipart/x-mixed-replace; boundary=frame",
    )
    response["Access-Control-Allow-Origin"] = "*"
    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


# ------------------------------------------------------------------
# Captura de foto
# ------------------------------------------------------------------

@api_view(['GET'])
def capture_frame(request, hw_idx: int):
    frame = camera_hub_instance.get_frame(int(hw_idx))
    if frame is None:
        return HttpResponse(b"Camara no disponible", status=503)
    ret, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
    if not ret:
        return HttpResponse(b"Error al codificar frame", status=500)
    response = HttpResponse(buffer.tobytes(), content_type="image/jpeg")
    response["Access-Control-Allow-Origin"] = "*"
    return response