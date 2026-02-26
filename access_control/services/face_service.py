import numpy as np
import face_recognition
from users_hub.models import Usuario


class FaceService:
    """
    Servicio encargado del reconocimiento facial.
    """

    UMBRAL_ACCESO = 0.45

    @staticmethod
    def detectar_y_codificar(image):
        """
        Detecta rostros y devuelve embeddings.
        """
        locations = face_recognition.face_locations(image)
        embeddings = face_recognition.face_encodings(image, locations)
        return embeddings

    @staticmethod
    def buscar_coincidencia(vector):
        """
        Compara el vector recibido contra la base de datos.
        """
        usuarios = Usuario.objects.exclude(face_embedding__isnull=True)

        mejor_match = None
        min_dist = FaceService.UMBRAL_ACCESO

        for usuario in usuarios:
            dist = face_recognition.face_distance(
                [np.array(usuario.face_embedding)],
                vector
            )[0]

            if dist < min_dist:
                min_dist = dist
                mejor_match = usuario

        return mejor_match, min_dist
