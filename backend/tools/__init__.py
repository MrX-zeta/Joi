from . import system, tasks, reminders, gcalendar, gmail

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
                "description": "Obtiene la hora actual real del sistema. Úsala SIEMPRE que Luis pregunte la hora, qué hora es, o necesites la hora actual. No estimes la hora tú mismo.",
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
                "description": "Obtiene la fecha actual real del sistema. Úsala SIEMPRE que Luis pregunte el día, la fecha, qué día es, o necesites la fecha actual. No estimes la fecha tú mismo.",
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
    "add_task": {
        "fn": tasks.add_task,
        "requires_confirmation": False,
        "schema": {
            "type": "function",
            "function": {
                "name": "add_task",
                "description": "Guarda UNA tarea NUEVA. Úsala SOLO cuando Luis pide anotar algo por primera vez. NUNCA la uses si Luis dice que YA terminó o completó algo.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "La tarea a guardar, por ejemplo 'entregar el proyecto de física'."},
                    },
                    "required": ["title"],
                },
            },
        },
    },
    "list_tasks": {
        "fn": tasks.list_tasks,
        "requires_confirmation": False,
        "schema": {
            "type": "function",
            "function": {
                "name": "list_tasks",
                "description": "Lista las tareas pendientes de Luis. Úsala cuando pregunte qué tiene pendiente, qué tareas tiene o qué debe hacer.",
                "parameters": {"type": "object", "properties": {}},
            },
        },
    },
    "complete_task": {
        "fn": tasks.complete_task,
        "requires_confirmation": False,
        "schema": {
            "type": "function",
            "function": {
                "name": "complete_task",
                "description": "Marca una tarea existente como COMPLETADA. Úsala SIEMPRE que Luis diga 'ya terminé', 'ya hice', 'completé' o 'listo' sobre una tarea. NUNCA uses add_task en ese caso.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Texto de la tarea que completó."},
                    },
                    "required": ["title"],
                },
            },
        },
    },
    "add_reminder": {
        "fn": reminders.add_reminder,
        "requires_confirmation": False,
        "schema": {
            "type": "function",
            "function": {
                "name": "add_reminder",
                "description": "Crea un recordatorio con hora. Úsala cuando Luis pida que le recuerdes algo a una hora o tiempo específico (ej. 'recuérdame llamar a las 5', 'avísame en 20 minutos').",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Qué recordar, ej. 'llamar a mamá'."},
                        "when": {"type": "string", "description": "Cuándo, en lenguaje natural, ej. 'a las 5', 'en 10 minutos', 'mañana a las 3'."},
                    },
                    "required": ["text", "when"],
                },
            },
        },
    },
    "list_reminders": {
        "fn": reminders.list_reminders,
        "requires_confirmation": False,
        "schema": {
            "type": "function",
            "function": {
                "name": "list_reminders",
                "description": "Lista los recordatorios pendientes de Luis. Úsala cuando pregunte qué recordatorios o avisos tiene.",
                "parameters": {"type": "object", "properties": {}},
            },
        },
    },
    "list_calendar_events": {
        "fn": gcalendar.list_calendar_events,
        "requires_confirmation": False,
        "schema": {
            "type": "function",
            "function": {
                "name": "list_calendar_events",
                "description": "Consulta el calendario de Google de Luis: sus eventos, agenda, citas, reuniones o lo que tiene programado. Úsala SIEMPRE que pregunte por su agenda, su calendario, qué tiene esta semana, o qué tiene programado. NUNCA digas que no tienes acceso al calendario: SÍ tienes esta herramienta.",
                "parameters": {"type": "object", "properties": {}},
            },
        },
    },
    "create_calendar_event": {
        "fn": gcalendar.create_calendar_event,
        "requires_confirmation": True,
        "schema": {
            "type": "function",
            "function": {
                "name": "create_calendar_event",
                "description": "Crea un evento nuevo en el calendario de Google de Luis. Úsala cuando pida agendar, programar o crear una reunión, cita o evento con fecha y hora.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Título del evento."},
                        "day": {"type": "string", "description": "El día: 'hoy', 'mañana', 'domingo', 'el viernes', o una fecha."},
                        "start_time": {"type": "string", "description": "Hora de inicio en formato 24h, ej. '11:30', '17:00'."},
                        "end_time": {"type": "string", "description": "Hora de fin en formato 24h, ej. '14:00'. Opcional."},
                    },
                    "required": ["title", "day", "start_time"],
                },
            },
        },
    },
    "get_datetime": {
        "fn": system.get_datetime,
        "requires_confirmation": False,
        "schema": {
            "type": "function",
            "function": {
                "name": "get_datetime",
                "description": "Obtiene la fecha Y la hora actuales juntas. Úsala SIEMPRE que Luis pregunte el día, la fecha, la hora, o cualquier combinación. NUNCA respondas fecha u hora de memoria.",
                "parameters": {"type": "object", "properties": {}},
            },
        },
    },
    "revisar_correo": {
        "fn": gmail.revisar_correo,
        "requires_confirmation": False,
        "schema": {
            "type": "function",
            "function": {
                "name": "revisar_correo",
                "description": "Revisa el Gmail de Luis. Sin parámetros lee sus correos sin leer recientes. Con 'query' busca correos de un remitente (persona o empresa), asunto o palabra clave. Úsala SIEMPRE que Luis pregunte por su correo, si tiene correos nuevos, o si tiene correos de alguien o sobre algún tema. NUNCA inventes correos.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Opcional. A quién o qué buscar (ej. 'Horacio Cisneros', 'JetBrains', 'factura'). Déjalo vacío para leer los no leídos."},
                    },
                },
            },
        },
    },
}

# Tools cuyo resultado ya está listo para el usuario: se devuelve tal cual,
# sin que el LLM lo reformule (evita que qwen cambie el formato o alucine).
DIRECT_REPLY_TOOLS = {
    "list_calendar_events",
    "create_calendar_event",
    "get_datetime",
    "get_time",
    "get_date",
    "add_reminder",
    "list_reminders",
    "revisar_correo",
}

def is_direct_reply(name: str) -> bool:
    return name in DIRECT_REPLY_TOOLS

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