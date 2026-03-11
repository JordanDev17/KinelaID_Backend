import cv2
import base64
import requests
import time

# =========================
# CONFIG
# =========================

STREAM_URL = "http://127.0.0.1:8000/api/cameras/stream/0/"

API_ACCESS = "http://127.0.0.1:8000/api/access/verificar-live/"
API_USERS = "http://127.0.0.1:8000/api/users/empleados/"
API_ROLES = "http://127.0.0.1:8000/api/users/roles/"
API_AREAS = "http://127.0.0.1:8000/api/audit/areas/"

# =========================
# UTILIDADES
# =========================

def frame_to_base64(frame):
    _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return f"data:image/jpeg;base64,{base64.b64encode(buffer).decode()}"

def seleccionar_opcion(lista, label):

    print(f"\n--- SELECCIONE {label} ---")

    for i, item in enumerate(lista, start=1):
        print(f"[{i}] {item.get('nombre', 'Sin nombre')}")

    while True:
        try:
            opc = input(f"Seleccione número (1-{len(lista)}): ")
            idx = int(opc) - 1

            if 0 <= idx < len(lista):
                return lista[idx]

        except ValueError:
            pass

        print("❌ Opción inválida")


# =========================
# MONITOR STREAMING
# =========================

def monitor_stream():

    print("🔌 Conectando al stream CCTV...")

    cap = cv2.VideoCapture(STREAM_URL)

    if not cap.isOpened():
        print("❌ No se pudo abrir el stream")
        return

    print("\n" + "="*30)
    print("--- KINELAID FAST MONITOR (STREAM MODE) ---")
    print("[A] Acceso  |  [R] Registro  |  [Q] Salir")
    print("="*30 + "\n")

    while True:

        ret, frame = cap.read()

        if not ret:
            print("⚠ Frame perdido, reconectando...")
            cap.release()
            time.sleep(2)
            cap = cv2.VideoCapture(STREAM_URL)
            continue

        # ----------------------
        # UI Overlay
        # ----------------------

        display_frame = frame.copy()

        h, w, _ = display_frame.shape

        cv2.rectangle(
            display_frame,
            (w // 4, h // 6),
            (3 * w // 4, 5 * h // 6),
            (0, 255, 255),
            2
        )

        cv2.putText(
            display_frame,
            "LISTO PARA CAPTURA",
            (w // 4, h // 6 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 255),
            1
        )

        cv2.imshow("KinelaID Control (Stream)", display_frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break

        if key in [ord("r"), ord("a")]:

            foto_b64 = frame_to_base64(frame)

            tipo_accion = "REGISTRO" if key == ord("r") else "ACCESO"

            print(f"\n📸 Captura de {tipo_accion} tomada.")
            print("👉 Cambie a la CONSOLA para completar datos.")

            try:

                # =========================
                # REGISTRO
                # =========================

                if key == ord("r"):

                    print("\n📋 REGISTRO DE USUARIO")

                    nombre = input("Nombre completo: ")
                    identificacion = input("Identificación: ")

                    res_roles = requests.get(API_ROLES)
                    roles = res_roles.json()

                    if roles:

                        rol = seleccionar_opcion(roles, "ROL")

                        payload = {
                            "nombre_completo": nombre,
                            "identificacion": identificacion,
                            "rol": rol["rol_id"],
                            "foto_registro": foto_b64
                        }

                        res = requests.post(API_USERS, json=payload)

                        print("📡 SERVER REGISTRO:", res.json())

                # =========================
                # ACCESO
                # =========================

                elif key == ord("a"):

                    print("\n🚪 ACCESO A ÁREA")

                    res_areas = requests.get(API_AREAS)
                    areas = res_areas.json()

                    if areas:

                        area = seleccionar_opcion(areas, "ÁREA")

                        payload = {
                            "foto": foto_b64,
                            "area_id": area["area_id"]
                        }

                        res = requests.post(API_ACCESS, json=payload)

                        print("📡 SERVER ACCESO:", res.json())

            except Exception as e:

                print(f"❌ Error comunicación: {e}")

            print("\n✅ Proceso terminado.\n")

            time.sleep(1)

    cap.release()
    cv2.destroyAllWindows()


# =========================
# MAIN
# =========================

if __name__ == "__main__":
    monitor_stream()