# camera_hub/apps.py

from django.apps import AppConfig
import os
import threading


class CameraHubConfig(AppConfig):

    default_auto_field = "django.db.models.BigAutoField"
    name = "camera_hub"

    def ready(self):

        # evita doble inicialización por autoreloader
        if os.environ.get("RUN_MAIN") != "true":
            return

        from .camera_manager import camera_hub_instance

        print("Inicializando cámaras KinelaID...")

        threading.Thread(
            target=camera_hub_instance.initialize_all_cameras,
            daemon=True
        ).start()