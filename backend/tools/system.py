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
    "spotify": {"cmds": ["explorer spotify:"], "proc": "Spotify.exe", "window": "Spotify"},
    "brave": {"cmds": [r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe", "start brave"], "proc": "brave.exe", "window": "Brave"},
    "navegador": {"cmds": [r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe", "start brave"], "proc": "brave.exe", "window": "Brave"},
    "calculadora": {"cmds": ["calc"], "proc": "CalculatorApp.exe", "window": "Calculadora"},
    "bloc de notas": {"cmds": ["notepad"], "proc": "notepad.exe", "window": "Bloc de notas"},
    "explorador": {"cmds": ["explorer"], "proc": "explorer.exe", "window": ""},
    "vscode": {"cmds": ["code"], "proc": "Code.exe", "window": "Visual Studio Code"},
    "visual studio code": {"cmds": ["code"], "proc": "Code.exe", "window": "Visual Studio Code"},
    "figma": {"cmds": [r"C:\Users\brian\AppData\Local\Figma\app-126.4.11\Figma.exe", r"C:\Users\brian\AppData\Local\Figma\Figma.exe"], "proc": "Figma.exe", "window": "Figma"},
    "teams": {"cmds": ["explorer msteams:", "start msteams:"], "proc": "ms-teams.exe", "window": "Microsoft Teams"},
    "microsoft teams": {"cmds": ["explorer msteams:", "start msteams:"], "proc": "ms-teams.exe", "window": "Microsoft Teams"},
}

# Sitios web permitidos: nombre → URL. Se abren en el navegador.
ALLOWED_SITES = {
    "classroom": "https://classroom.google.com",
    "gmail": "https://mail.google.com",
    "correo": "https://mail.google.com",
    "github": "https://github.com",
    "whatsapp": "https://web.whatsapp.com",
    "youtube": "https://youtube.com",
    "drive": "https://drive.google.com",
}

def open_url(site: str = "", **kwargs) -> str:
    """Abre un sitio web permitido en el navegador."""
    key = site.lower().strip()
    # Si en realidad es una app de escritorio, redirige a open_app
    if key in ALLOWED_APPS:
        return open_app(key)
    # Coincidencia flexible: tolera errores de transcripción
    if key not in ALLOWED_SITES:
        for known in ALLOWED_SITES:
            if known in key or key in known or _similar(key, known):
                key = known
                break
    url = ALLOWED_SITES.get(key)
    if not url:
        disponibles = ", ".join(sorted(ALLOWED_SITES.keys()))
        return f"No tengo ese sitio. Disponibles: {disponibles}."
    try:
        import webbrowser
        webbrowser.open(url)
        return f"Abrí {key} en el navegador."
    except Exception as e:
        return f"No pude abrir {key}: {e}"


def _similar(a: str, b: str) -> bool:
    """Coincidencia aproximada simple para tolerar errores de STT."""
    from difflib import SequenceMatcher
    return SequenceMatcher(None, a, b).ratio() > 0.6

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

def _focus_window(title_hint: str) -> bool:
    """Trae al frente la primera ventana cuyo título contenga title_hint."""
    if not title_hint:
        return False
    try:
        import pygetwindow as gw
        wins = [w for w in gw.getAllWindows()
                if title_hint.lower() in w.title.lower() and w.title.strip()]
        if not wins:
            return False
        w = wins[0]

        try:
            import win32gui
            import win32con
            hwnd = w._hWnd
            # Si está minimizada, restáurala; si no, déjala como está
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
        except Exception:
            if w.isMinimized:
                w.restore()
            w.activate()
        return True
    except Exception:
        pass
    return False

def open_app(name: str = "", **kwargs) -> str:
    """Abre una aplicación del sistema, o la trae al frente si ya está abierta."""
    key = name.lower().strip()
    app = ALLOWED_APPS.get(key)

    # Coincidencia flexible: tolera errores de transcripción (Tims→teams, etc.)
    if not app:
        for known in ALLOWED_APPS:
            if known in key or key in known or _similar(key, known):
                key = known
                app = ALLOWED_APPS[known]
                break

    if not app:
        disponibles = ", ".join(sorted(set(ALLOWED_APPS.keys())))
        return f"No puedo abrir '{name}'. Apps disponibles: {disponibles}."

    # Si ya está abierta, tráela al frente
    if app.get("proc") and _is_running(app["proc"]):
        if _focus_window(app.get("window", "")):
            return f"Traje {name} al frente."
        return f"{name} ya está abierta."

    for cmd in app["cmds"]:
        try:
            if cmd.lower().endswith(".exe"):
                subprocess.Popen(f'"{cmd}"', shell=True)
                return f"Abrí {name}."
            exe = cmd.split()[0]
            if exe in ("start", "explorer") or shutil.which(exe):
                subprocess.Popen(cmd, shell=True)
                return f"Abrí {name}."
        except Exception:
            continue

    return f"No encontré cómo abrir {name} en tu sistema."