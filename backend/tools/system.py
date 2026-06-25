import subprocess
import shutil
from datetime import datetime


def get_time(**kwargs) -> str:
    """Devuelve la hora actual."""
    now = datetime.now()
    return now.strftime("Son las %H:%M.")


def get_date(**kwargs) -> str:
    """Devuelve la fecha actual."""
    now = datetime.now()
    dias = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
             "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    return f"Hoy es {dias[now.weekday()]} {now.day} de {meses[now.month-1]} de {now.year}."


# Mapa de apps permitidas. Cada una: comandos a intentar + nombre de proceso para detectar si ya corre.
ALLOWED_APPS = {
    "spotify": {"cmds": ["explorer spotify:"], "proc": "Spotify.exe"},
    "brave": {"cmds": [r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe", "start brave"], "proc": "brave.exe"},
    "navegador": {"cmds": [r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe", "start brave"], "proc": "brave.exe"},
    "calculadora": {"cmds": ["calc"], "proc": "CalculatorApp.exe"},
    "bloc de notas": {"cmds": ["notepad"], "proc": "notepad.exe"},
    "explorador": {"cmds": ["explorer"], "proc": "explorer.exe"},
    "vscode": {"cmds": ["code"], "proc": "Code.exe"},
    "visual studio code": {"cmds": ["code"], "proc": "Code.exe"},
}


def _is_running(proc_name: str) -> bool:
    """Verifica si un proceso está corriendo (por nombre de ejecutable)."""
    try:
        import psutil
        proc_lower = proc_name.lower()
        for p in psutil.process_iter(["name"]):
            if p.info["name"] and p.info["name"].lower() == proc_lower:
                return True
    except ImportError:
        pass
    return False


def open_app(name: str = "", **kwargs) -> str:
    """Abre una aplicación del sistema (solo apps permitidas)."""
    key = name.lower().strip()
    app = ALLOWED_APPS.get(key)
    if not app:
        disponibles = ", ".join(sorted(set(ALLOWED_APPS.keys())))
        return f"No puedo abrir '{name}'. Apps disponibles: {disponibles}."

    # ¿Ya está abierta?
    if app.get("proc") and _is_running(app["proc"]):
        return f"{name} ya está abierta."

    for cmd in app["cmds"]:
        try:
            # Si es ruta directa a .exe, lánzala tal cual
            if cmd.lower().endswith(".exe"):
                subprocess.Popen(f'"{cmd}"', shell=True)
                return f"Abrí {name}."
            # Comandos especiales que no necesitan estar en PATH
            exe = cmd.split()[0]
            if exe in ("start", "explorer") or shutil.which(exe):
                subprocess.Popen(cmd, shell=True)
                return f"Abrí {name}."
        except Exception:
            continue

    return f"No encontré cómo abrir {name} en tu sistema."