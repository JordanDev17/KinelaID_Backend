import base64
from django.core.files.base import ContentFile
import face_recognition


class ImageService:
    """
    Servicio encargado de decodificar y cargar imágenes.
    """

    @staticmethod
    def decode_base64_image(foto_b64):
        """
        Convierte una imagen Base64 en un array RGB usable por face_recognition.
        """
        try:
            _, imgstr = foto_b64.split(';base64,')
            data = ContentFile(base64.b64decode(imgstr))
            return face_recognition.load_image_file(data)
        except Exception:
            return None
