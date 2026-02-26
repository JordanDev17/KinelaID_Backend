from rest_framework.permissions import BasePermission

ROLES_CON_EXPORTACION = ['Gerente', 'Administrador', 'Auditor']


class PuedeExportarAuditoria(BasePermission):
    """
    Permite exportar registros de auditoría
    solo a roles autorizados
    """

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        # Asumiendo que Usuario tiene FK a Rol
        return (
            hasattr(user, 'rol')
            and user.rol.nombre in ROLES_CON_EXPORTACION
        )
