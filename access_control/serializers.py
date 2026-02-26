from rest_framework import serializers
from audit_log.models import Area

class AccesoLiveSerializer(serializers.Serializer):
    # Validamos que el Base64 no venga vacío
    foto = serializers.CharField(required=True, help_text="Imagen en formato Base64")
    
    # Validamos que el área enviada exista en la DB
    area_id = serializers.IntegerField(required=True)

    def validate_area_id(self, value):
        if not Area.objects.filter(area_id=value).exists():
            raise serializers.ValidationError("El área especificada no existe en el sistema.")
        return value

    def validate_foto(self, value):
        if not value.startswith('data:image/jpeg;base64,'):
            # Opcional: podrías ser más flexible, pero esto asegura el estándar que usas
            if not value.startswith('data:image/png;base64,'):
                 raise serializers.ValidationError("La imagen debe estar en formato Base64 válido (Data URI).")
        return value