from . import system

# Registro central de herramientas.
# Cada entrada: el esquema (para el LLM) + la función real + flag de confirmación.
TOOLS = {
    "get_time": {
        "fn": system.get_time,
        "requires_confirmation": False,
        "schema": {
            "type": "function",
            "function": {
                "name": "get_time",
                "description": "Obtiene la hora actual. Úsala cuando Luis pregunte qué hora es.",
                "parameters": {"type": "object", "properties": {}},
            },
        },
    },
    "get_date": {
        "fn": system.get_date,
        "requires_confirmation": False,
        "schema": {
            "type": "function",
            "function": {
                "name": "get_date",
                "description": "Obtiene la fecha actual. Úsala cuando Luis pregunte qué día es o la fecha.",
                "parameters": {"type": "object", "properties": {}},
            },
        },
    },
    "open_app": {
        "fn": system.open_app,
        "requires_confirmation": True,
        "schema": {
            "type": "function",
            "function": {
                "name": "open_app",
                "description": "Abre una aplicación en la computadora de Luis. Úsala cuando pida abrir un programa.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Abre o trae al frente un PROGRAMA DE ESCRITORIO: Spotify, Figma, VSCode, Brave, Teams, calculadora. Úsala también cuando Luis diga 'trae al frente' o 'cambia a' una de estas apps. NO la uses para sitios web como Classroom o Gmail.",
                        },
                    },
                    "required": ["name"],
                },
            },
        },
    },
    "open_url": {
        "fn": system.open_url,
        "requires_confirmation": True,
        "schema": {
            "type": "function",
            "function": {
                "name": "open_url",
                "description": "Abre un sitio web en el navegador de Luis (Classroom, Gmail, GitHub, WhatsApp, etc.). Úsala cuando pida abrir alguno de esos servicios.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "site": {
                            "type": "string",
                             "description": "Abre un SITIO WEB dentro del navegador: Classroom, Gmail, GitHub, WhatsApp, YouTube, Drive. Solo para esos sitios. NO la uses para abrir el navegador Brave en sí (para eso usa open_app).",
                        },
                    },
                    "required": ["site"],
                },
            },
        },
    },
}


def get_schemas() -> list[dict]:
    """Lista de esquemas para pasar a Ollama."""
    return [t["schema"] for t in TOOLS.values()]


def execute(name: str, args: dict) -> str:
    """Ejecuta una herramienta por nombre. Devuelve su resultado como texto."""
    tool = TOOLS.get(name)
    if not tool:
        return f"Error: herramienta '{name}' no existe."
    try:
        return tool["fn"](**(args or {}))
    except Exception as e:
        return f"Error al ejecutar '{name}': {e}"


def requires_confirmation(name: str) -> bool:
    tool = TOOLS.get(name)
    return tool["requires_confirmation"] if tool else False