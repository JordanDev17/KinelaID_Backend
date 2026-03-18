from rest_framework import serializers
from audit_log.models import Area


class AccesoLiveSerializer(serializers.Serializer):
    """
    Serializer para validar solicitudes de acceso biométrico.
    """

    foto = serializers.CharField(
        required=True,
        help_text="Imagen en Base64 (Data URI)"
    )

    area_id = serializers.IntegerField(required=True)

    def validate_area_id(self, value):

        if not Area.objects.filter(area_id=value).exists():

            raise serializers.ValidationError(
                "El área especificada no existe"
            )

        return value

    def validate_foto(self, value):

        if not value.startswith("data:image"):

            raise serializers.ValidationError(
                "Formato Base64 inválido"
            )

        return value