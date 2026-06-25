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
                            "description": "Nombre de la app a abrir, por ejemplo 'spotify' o 'navegador'.",
                        },
                    },
                    "required": ["name"],
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