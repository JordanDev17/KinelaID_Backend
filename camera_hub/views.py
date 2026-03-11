# camera_hub/views.py

import cv2
import time

from django.http import StreamingHttpResponse, HttpResponse

from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Camara
from .serializers import CamaraSerializer
from .camera_manager import camera_hub_instance


# -----------------------------
# CRUD cámaras
# -----------------------------

class CamaraListCreateView(generics.ListCreateAPIView):
    queryset = Camara.objects.all()
    serializer_class = CamaraSerializer


class CamaraDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Camara.objects.all()
    serializer_class = CamaraSerializer


# -----------------------------
# Detectar cámaras físicas
# -----------------------------

@api_view(['GET'])
def detectar_camaras_fisicas(request):

    disponibles = []

    for i in range(10):

        cap = cv2.VideoCapture(i)

        if cap.isOpened():

            ret, frame = cap.read()

            if ret:
                disponibles.append({
                    "index": i,
                    "label": f"Camara USB {i}"
                })

            cap.release()

    return Response(disponibles)


# -----------------------------
# Generador de streaming MJPEG
# -----------------------------

def gen_shared_frames(hw_idx):

    while True:

        frame = camera_hub_instance.get_frame(hw_idx)

        if frame is None:
            time.sleep(0.05)
            continue

        ret, buffer = cv2.imencode(
            ".jpg",
            frame,
            [cv2.IMWRITE_JPEG_QUALITY, 70]
        )

        if not ret:
            continue

        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n'
            + buffer.tobytes() +
            b'\r\n'
        )


# -----------------------------
# Endpoint streaming CCTV
# -----------------------------

class VideoStreamView(APIView):

    def get(self, request, cam_idx):

        idx = int(cam_idx)

        return StreamingHttpResponse(
            gen_shared_frames(idx),
            content_type='multipart/x-mixed-replace; boundary=frame'
        )


# -----------------------------
# Captura frame único
# -----------------------------

@api_view(['GET'])
def capture_frame(request, hw_idx):

    frame = camera_hub_instance.get_frame(int(hw_idx))

    if frame is None:
        return HttpResponse(b"Camara no disponible", status=503)

    ret, buffer = cv2.imencode(
        ".jpg",
        frame,
        [cv2.IMWRITE_JPEG_QUALITY, 90]
    )

    if not ret:
        return HttpResponse(b"Error de captura", status=503)

    return HttpResponse(buffer.tobytes(), content_type="image/jpeg")