from audit_log.models import RegistroAcceso, Area, PermisoArea
from .face_service import FaceService

class AccessService:
    """
    Servicio que decide si un acceso es aprobado o denegado 
    basado en biometría y permisos de Rol/Área.
    """

    @staticmethod
    def procesar_acceso(area_id, embeddings, ip_origen):
        try:
            area = Area.objects.get(area_id=area_id)
        except Area.DoesNotExist:
            return False, "Área no configurada", None

        if not embeddings:
            AccessService._log(area, None, "DENEGADO", "No se detectó rostro", ip_origen)
            return False, "Rostro no visible", None

        # Buscamos al usuario por biometría
        usuario, dist = FaceService.buscar_coincidencia(embeddings[0])

        if usuario and usuario.activo:
            # ==========================================
            # VALIDACIÓN DE PERMISOS POR ROL Y ÁREA
            # ==========================================
            permiso = PermisoArea.objects.filter(rol=usuario.rol, area=area).first()
            
            # Si no existe el registro de permiso o 'puede_acceder' es False
            if not permiso or not permiso.puede_acceder:
                motivo = f"Rol {usuario.rol.nombre} no autorizado para {area.nombre}"
                AccessService._log(area, usuario, "DENEGADO", motivo, ip_origen, permitido=False)
                return False, motivo, None

            # Acceso Exitoso
            confianza = round(1 - dist, 3)
            AccessService._log(area, usuario, "APROBADO", None, ip_origen, permitido=True)
            
            return True, usuario, confianza

        # Usuario no reconocido en la base de datos
        AccessService._log(area, None, "DENEGADO", "Usuario no reconocido", ip_origen)
        return False, "Acceso denegado: Usuario no registrado", None

    @staticmethod
    def _log(area, usuario, estado, motivo, ip, permitido=False):
        """Guarda el evento en audit_log."""
        RegistroAcceso.objects.create(
            usuario=usuario,
            rol=usuario.rol if usuario else None,
            area=area,
            estado=estado,
            permitido=permitido,
            motivo_denegacion=motivo
        )