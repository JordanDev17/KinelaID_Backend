import base64
import cv2
import numpy as np
from django.core.files.base import ContentFile
import face_recognition


class ImageService:
    """
    Servicio encargado de decodificar y cargar imágenes.
    """

    @staticmethod
    def decode_base64_image(foto_b64):
        try:
            _, imgstr = foto_b64.split(';base64,')
            data = base64.b64decode(imgstr)

            # Decodificar con OpenCV para poder preprocesar
            arr = np.frombuffer(data, np.uint8)
            bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if bgr is None:
                return None

            # Normalizar brillo y contraste (CLAHE en canal L de LAB)
            lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            lab = cv2.merge([l, a, b])
            bgr = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

            # face_recognition espera RGB
            return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

        except Exception:
            return None