from audit_log.models import RegistroAcceso, Area
from .face_service import FaceService


class AccessService:
    """
    Servicio que decide si un acceso es aprobado o denegado.
    """

    @staticmethod
    def procesar_acceso(area_id, embeddings, ip_origen):
        area = Area.objects.get(area_id=area_id)

        if not embeddings:
            AccessService._log(area, None, "DENEGADO", "No se detectó rostro", ip_origen)
            return False, "Rostro no visible", None

        usuario, dist = FaceService.buscar_coincidencia(embeddings[0])

        if usuario and usuario.activo:
            AccessService._log(area, usuario, "APROBADO", None, ip_origen, dist)
            return True, usuario.nombre_completo, round(1 - dist, 3)

        AccessService._log(area, None, "DENEGADO", "Usuario no reconocido", ip_origen)
        return False, "Acceso no autorizado", None

    @staticmethod
    def _log(area, usuario, estado, motivo, ip, dist=None):
        RegistroAcceso.objects.create(
            usuario=usuario,
            area=area,
            estado=estado,
            motivo_denegacion=motivo,
            score_confianza=(1 - dist) if dist else None,
        )
