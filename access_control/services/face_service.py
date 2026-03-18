import logging
import numpy as np
import face_recognition

from users_hub.models import Usuario


logger = logging.getLogger(__name__)


class FaceService:
    """
    Servicio encargado del reconocimiento facial.
    """

    # Umbral biométrico
    UMBRAL_ACCESO = 0.45

    @staticmethod
    def detectar_y_codificar(image):
        """
        Detecta rostros y genera embeddings.
        """

        locations = face_recognition.face_locations(image)

        logger.debug(f"Rostros detectados: {len(locations)}")

        embeddings = face_recognition.face_encodings(image, locations)

        return embeddings

    @staticmethod
    def buscar_coincidencia(vector):
        """
        Busca coincidencia biométrica en la base de datos.
        """

        usuarios = Usuario.objects.exclude(face_embedding__isnull=True)

        mejor_usuario = None
        mejor_dist = FaceService.UMBRAL_ACCESO

        for usuario in usuarios:

            try:

                embedding_db = np.array(usuario.face_embedding)

                if embedding_db.shape[0] != 128:
                    continue

                dist = face_recognition.face_distance(
                    [embedding_db],
                    vector
                )[0]

                if dist < mejor_dist:

                    mejor_dist = dist
                    mejor_usuario = usuario

            except Exception as e:

                logger.warning(
                    f"Error comparando embedding usuario {usuario.usuario_id}"
                )

        return mejor_usuario, mejor_dist