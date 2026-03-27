import logging
import numpy as np
import face_recognition
from users_hub.models import Usuario

logger = logging.getLogger(__name__)

class FaceService:
    UMBRAL_ACCESO   = 0.45  # Estricto — para acceso en vivo
    UMBRAL_REGISTRO = 0.60  # Más amplio — para detectar duplicados al registrar

    @staticmethod
    def detectar_y_codificar(image):
        locations = face_recognition.face_locations(image)
        logger.debug(f"Rostros detectados: {len(locations)}")
        return face_recognition.face_encodings(image, locations)

    @staticmethod
    def buscar_coincidencia(vector, umbral=None):
        """
        Busca coincidencia biométrica en la base de datos.
        Acepta umbral personalizado para diferenciar acceso vs. registro.
        """
        if umbral is None:
            umbral = FaceService.UMBRAL_ACCESO

        usuarios = Usuario.objects.exclude(face_embedding__isnull=True)
        mejor_usuario = None
        mejor_dist = umbral  # Solo retorna match si está por debajo de este umbral

        for usuario in usuarios:
            try:
                embedding_db = np.array(usuario.face_embedding)
                if embedding_db.shape[0] != 128:
                    continue

                dist = face_recognition.face_distance([embedding_db], vector)[0]

                if dist < mejor_dist:
                    mejor_dist = dist
                    mejor_usuario = usuario

            except Exception:
                logger.warning(f"Error comparando embedding usuario {usuario.usuario_id}")

        return mejor_usuario, mejor_dist