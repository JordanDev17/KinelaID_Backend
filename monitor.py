import cv2
import base64
import requests
import time

# ======================================================
# CONFIGURACIÓN
# ======================================================

BASE_URL = "http://127.0.0.1:8000/api"

STREAM_URL = f"{BASE_URL}/cameras/stream/0/"

API_ACCESS = f"{BASE_URL}/access/verificar-live/"
API_REGISTER = f"{BASE_URL}/access/registrar-empleado/"

API_ROLES = f"{BASE_URL}/users/roles/"
API_AREAS = f"{BASE_URL}/audit/areas/"

RECONNECT_DELAY = 2


# ======================================================
# UTILIDADES
# ======================================================

def frame_to_base64(frame):
    """
    Convierte un frame OpenCV a Base64 para enviarlo al backend.
    """

    _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 90])

    return f"data:image/jpeg;base64,{base64.b64encode(buffer).decode()}"


def seleccionar_opcion(lista, label):

    print(f"\n--- SELECCIONE {label} ---")

    for i, item in enumerate(lista, start=1):

        nombre = item.get("nombre", "Sin nombre")

        print(f"[{i}] {nombre}")

    while True:

        try:

            opc = int(input(f"Seleccione número (1-{len(lista)}): ")) - 1

            if 0 <= opc < len(lista):
                return lista[opc]

        except:
            pass

        print("❌ Opción inválida")


# ======================================================
# STREAM
# ======================================================

def conectar_stream():

    print("🔌 Conectando al streaming CCTV...")

    cap = cv2.VideoCapture(STREAM_URL)

    if not cap.isOpened():

        print("❌ No se pudo abrir el stream")

        return None

    print("✅ Stream conectado")

    return cap


# ======================================================
# REGISTRO EMPLEADO
# ======================================================

def registrar_empleado(frame):

    print("\n📋 REGISTRO DE EMPLEADO")

    nombre = input("Nombre completo: ")
    identificacion = input("Identificación: ")

    try:

        res_roles = requests.get(API_ROLES)

        if res_roles.status_code != 200:

            print("❌ Error obteniendo roles")
            return

        roles = res_roles.json()

        rol = seleccionar_opcion(roles, "ROL")

        foto_b64 = frame_to_base64(frame)

        payload = {

            "nombre_completo": nombre,
            "identificacion": identificacion,
            "rol": rol["rol_id"],
            "foto_registro": foto_b64

        }

        res = requests.post(API_REGISTER, json=payload)

        print("📡 SERVER:", res.json())

    except Exception as e:

        print("❌ Error registro:", e)


# ======================================================
# ACCESO
# ======================================================

def verificar_acceso(frame):

    print("\n🚪 VERIFICACIÓN DE ACCESO")

    try:

        res_areas = requests.get(API_AREAS)

        if res_areas.status_code != 200:

            print("❌ Error obteniendo áreas")
            return

        areas = res_areas.json()

        area = seleccionar_opcion(areas, "ÁREA")

        foto_b64 = frame_to_base64(frame)

        payload = {

            "foto": foto_b64,
            "area_id": area["area_id"]

        }

        res = requests.post(API_ACCESS, json=payload)

        print("📡 SERVER:", res.json())

    except Exception as e:

        print("❌ Error acceso:", e)


# ======================================================
# UI OVERLAY
# ======================================================

def draw_overlay(frame):

    display = frame.copy()

    h, w, _ = display.shape

    # zona captura

    cv2.rectangle(
        display,
        (w // 4, h // 6),
        (3 * w // 4, 5 * h // 6),
        (0, 255, 255),
        2
    )

    cv2.putText(
        display,
        "ZONA DE CAPTURA",
        (w // 4, h // 6 - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 255, 255),
        2
    )

    # controles

    cv2.putText(
        display,
        "[R] REGISTRO  |  [A] ACCESO  |  [Q] SALIR",
        (20, h - 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 255, 0),
        2
    )

    return display


# ======================================================
# MONITOR STREAM
# ======================================================

def monitor_stream():

    cap = conectar_stream()

    if not cap:
        return

    print("\n==============================")
    print("  KINELAID DEVICE MONITOR")
    print("  STREAM MODE")
    print("==============================\n")

    while True:

        ret, frame = cap.read()

        if not ret:

            print("⚠ Frame perdido, reconectando...")

            cap.release()

            time.sleep(RECONNECT_DELAY)

            cap = conectar_stream()

            if not cap:
                return

            continue

        display = draw_overlay(frame)

        cv2.imshow("KinelaID Monitor", display)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break

        # =========================
        # CAPTURA
        # =========================

        if key in [ord("r"), ord("a")]:

            print("\n📸 Frame capturado")

            if key == ord("r"):
                registrar_empleado(frame)

            elif key == ord("a"):
                verificar_acceso(frame)

            print("\n✅ Operación finalizada\n")

            time.sleep(1)

    cap.release()
    cv2.destroyAllWindows()


# ======================================================
# MAIN
# ======================================================

if __name__ == "__main__":

    print("\n🚀 Iniciando KinelaID Monitor\n")

    monitor_stream()