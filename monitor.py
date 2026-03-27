import cv2
import base64
import requests
import time
import threading

# ======================================================
# CONFIGURACIÓN
# ======================================================

BASE_URL    = "http://127.0.0.1:8000/api"
STREAM_URL  = f"{BASE_URL}/cameras/stream/0/"
API_ACCESS  = f"{BASE_URL}/access/verificar-live/"
API_REGISTER= f"{BASE_URL}/access/registrar-empleado/"
API_ROLES   = f"{BASE_URL}/users/roles/"
API_AREAS   = f"{BASE_URL}/audit/areas/"

RECONNECT_DELAY = 2

# ======================================================
# ESTADO GLOBAL DE UI
# ======================================================

ui_state = {
    "mensaje":    "Listo",
    "sub":        "",
    "color":      (200, 200, 200),   # Gris neutro por defecto
    "procesando": False,
    "timestamp":  0,
    "confianza":  None,
    "usuario":    None,
}
ui_lock = threading.Lock()

def set_ui(mensaje, sub="", color=(200, 200, 200), confianza=None, usuario=None):
    with ui_lock:
        ui_state.update({
            "mensaje":   mensaje,
            "sub":       sub,
            "color":     color,
            "timestamp": time.time(),
            "confianza": confianza,
            "usuario":   usuario,
        })

def set_procesando(val: bool):
    with ui_lock:
        ui_state["procesando"] = val

# ======================================================
# UTILIDADES
# ======================================================

def frame_to_base64(frame):
    _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return f"data:image/jpeg;base64,{base64.b64encode(buffer).decode()}"

def seleccionar_opcion(lista, label):
    print(f"\n--- SELECCIONE {label} ---")
    for i, item in enumerate(lista, start=1):
        print(f"[{i}] {item.get('nombre', 'Sin nombre')}")
    while True:
        try:
            opc = int(input(f"Seleccione número (1-{len(lista)}): ")) - 1
            if 0 <= opc < len(lista):
                return lista[opc]
        except Exception:
            pass
        print("Opción inválida")

# ======================================================
# REGISTRO EMPLEADO  (en hilo separado)
# ======================================================

def registrar_empleado(frame):
    set_procesando(True)
    set_ui("Procesando registro...", color=(255, 200, 0))

    print("\n REGISTRO DE EMPLEADO")
    nombre        = input("Nombre completo: ")
    identificacion= input("Identificación: ")

    try:
        res_roles = requests.get(API_ROLES, timeout=5)
        roles     = res_roles.json()
        rol       = seleccionar_opcion(roles, "ROL")
        foto_b64  = frame_to_base64(frame)

        payload = {
            "nombre_completo": nombre,
            "identificacion":  identificacion,
            "rol":             rol["rol_id"],
            "foto_registro":   foto_b64,
        }

        res  = requests.post(API_REGISTER, json=payload, timeout=10)
        data = res.json()
        print("SERVER:", data)

        if res.status_code == 200 and data.get("status") == "SUCCESS":
            set_ui(
                f"Registro exitoso",
                sub=f"{data.get('nombre', '')}  |  ID: {data.get('usuario_id', '')}",
                color=(0, 220, 100),    # Verde
            )
        else:
            set_ui(
                "Registro fallido",
                sub=data.get("error", "Error desconocido"),
                color=(0, 60, 220),     # Rojo
            )

    except Exception as e:
        print("Error registro:", e)
        set_ui("Error de conexión", sub=str(e), color=(0, 60, 220))
    finally:
        set_procesando(False)

# ======================================================
# ACCESO  (en hilo separado)
# ======================================================

def verificar_acceso(frame):
    set_procesando(True)
    set_ui("Verificando acceso...", color=(255, 200, 0))

    print("\n VERIFICACIÓN DE ACCESO")
    try:
        res_areas = requests.get(API_AREAS, timeout=5)
        areas     = res_areas.json()
        area      = seleccionar_opcion(areas, "ÁREA")
        foto_b64  = frame_to_base64(frame)

        payload = {"foto": foto_b64, "area_id": area["area_id"]}
        res     = requests.post(API_ACCESS, json=payload, timeout=10)
        data    = res.json()
        print("SERVER:", data)

        if res.status_code == 200 and data.get("status") == "SUCCESS":
            ud = data.get("user_data", {})
            set_ui(
                "ACCESO APROBADO",
                sub=f"{ud.get('nombre','')}  |  {ud.get('rol','')}  |  Conf: {data.get('confidence', 0):.1%}",
                color=(0, 220, 100),    # Verde
                confianza=data.get("confidence"),
                usuario=ud,
            )
        else:
            set_ui(
                "ACCESO DENEGADO",
                sub=data.get("mensaje", data.get("error", "Sin motivo")),
                color=(0, 60, 220),     # Rojo
            )

    except Exception as e:
        print("Error acceso:", e)
        set_ui("Error de conexión", sub=str(e), color=(0, 60, 220))
    finally:
        set_procesando(False)

# ======================================================
# OVERLAY
# ======================================================

COLOR_CYAN  = (255, 220,   0)   # BGR
COLOR_WHITE = (255, 255, 255)
COLOR_DARK  = ( 20,  20,  20)

def draw_overlay(frame):
    display = frame.copy()
    h, w    = display.shape[:2]

    # ── Marco zona de captura ──────────────────────────────────────────────
    x1, y1 = w // 4,     h // 6
    x2, y2 = 3 * w // 4, 5 * h // 6
    cv2.rectangle(display, (x1, y1), (x2, y2), COLOR_CYAN, 2)
    cv2.putText(display, "ZONA DE CAPTURA", (x1 + 6, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, COLOR_CYAN, 1, cv2.LINE_AA)

    # ── Barra de controles (abajo) ─────────────────────────────────────────
    bar_h = 36
    cv2.rectangle(display, (0, h - bar_h), (w, h), COLOR_DARK, -1)
    cv2.putText(display,
                "[R] Registrar   [A] Acceso   [Q] Salir",
                (16, h - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, COLOR_WHITE, 1, cv2.LINE_AA)

    # ── Panel de estado (arriba) ───────────────────────────────────────────
    with ui_lock:
        estado     = dict(ui_state)

    elapsed = time.time() - estado["timestamp"]
    visible = elapsed < 5  # El mensaje desaparece a los 5 segundos

    # Spinner mientras procesa
    if estado["procesando"]:
        spinner = ["|", "/", "—", "\\"][int(time.time() * 6) % 4]
        cv2.rectangle(display, (0, 0), (w, 50), (30, 30, 30), -1)
        cv2.putText(display, f"{spinner}  Procesando...",
                    (16, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                    (255, 200, 0), 2, cv2.LINE_AA)

    elif visible:
        color = estado["color"]

        # Fondo semitransparente en la barra superior
        overlay = display.copy()
        cv2.rectangle(overlay, (0, 0), (w, 60), COLOR_DARK, -1)
        cv2.addWeighted(overlay, 0.6, display, 0.4, 0, display)

        # Línea de color indicadora (izquierda)
        cv2.rectangle(display, (0, 0), (6, 60), color, -1)

        # Texto principal
        cv2.putText(display, estado["mensaje"],
                    (16, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.75,
                    color, 2, cv2.LINE_AA)

        # Sub-texto (nombre, rol, motivo…)
        if estado["sub"]:
            cv2.putText(display, estado["sub"],
                        (16, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.50,
                        COLOR_WHITE, 1, cv2.LINE_AA)

        # Barra de confianza (solo en acceso aprobado)
        if estado["confianza"] is not None:
            bar_w    = 200
            bar_x, bar_y = w - bar_w - 20, 10
            filled   = int(bar_w * estado["confianza"])
            cv2.rectangle(display, (bar_x, bar_y), (bar_x + bar_w, bar_y + 18),
                          (60, 60, 60), -1)
            cv2.rectangle(display, (bar_x, bar_y), (bar_x + filled, bar_y + 18),
                          (0, 220, 100), -1)
            cv2.putText(display, f"Conf: {estado['confianza']:.1%}",
                        (bar_x, bar_y + 34),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, COLOR_WHITE, 1, cv2.LINE_AA)

    return display

# ======================================================
# STREAM PRINCIPAL
# ======================================================

def conectar_stream():
    print("Conectando al stream CCTV...")
    cap = cv2.VideoCapture(STREAM_URL)
    if not cap.isOpened():
        print("No se pudo abrir el stream")
        return None
    # Reducir buffer interno para minimizar latencia
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    print("Stream conectado")
    return cap

def monitor_stream():
    cap = conectar_stream()
    if not cap:
        return

    print("\n==============================")
    print("  KINELAID DEVICE MONITOR")
    print("==============================\n")

    set_ui("Listo — presiona [R] o [A]")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Frame perdido, reconectando...")
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

        # Solo lanza la acción si no hay una en curso
        if key in [ord("r"), ord("a")] and not ui_state["procesando"]:
            frozen = frame.copy()  # Congela el frame para enviarlo al API

            if key == ord("r"):
                t = threading.Thread(target=registrar_empleado, args=(frozen,), daemon=True)
            else:
                t = threading.Thread(target=verificar_acceso, args=(frozen,), daemon=True)

            t.start()

    cap.release()
    cv2.destroyAllWindows()

# ======================================================
# MAIN
# ======================================================

if __name__ == "__main__":
    print("\n Iniciando KinelaID Monitor\n")
    monitor_stream()