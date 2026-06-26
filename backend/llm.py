from ollama import AsyncClient
import tools
import json as _json
import re

MODEL = "qwen2.5:3b"
KEEP_ALIVE = -1

SYSTEM_PROMPT = (
    "Eres Joi, la asistente personal de Luis. Te diriges a él como Luis, en segunda persona "
    "('tú', 'tienes', 'tu reunión'), nunca en tercera persona. "
    "Personalidad femenina, cálida, cercana y directa. "
    "BREVEDAD: responde en 1 o 2 frases cortas, naturales para hablar. Sin listas ni preámbulos. "
    "Solo te extiendes si Luis lo pide explícitamente. Hablas español natural. "
    "\n\n"
    "HERRAMIENTAS: úsalas para datos reales (hora, fecha, tareas, recordatorios, calendario). "
    "Nunca escribas llamadas a herramientas como JSON en tu respuesta; el sistema las ejecuta. "
    "Ejecuta solo lo que Luis pide en su último mensaje; no repitas acciones anteriores. "
    "\n\n"
    "REGLA DE VERACIDAD (la más importante): solo puedes afirmar que algo existe o que una acción "
    "se completó si una herramienta te lo devolvió en este turno. Si la herramienta devolvió un error "
    "o un 'No entendí', comunícale ese error a Luis tal cual y NO digas que se completó. "
    "Nunca inventes eventos, reuniones, tareas, horas ni fechas. Si no tienes el dato, dilo. "
    "\n\n"
    "EJECUTA SIEMPRE LA HERRAMIENTA: cada vez que Luis pida abrir una app o un sitio, agendar, "
    "recordar o consultar algo, DEBES llamar a la herramienta correspondiente EN ESTE TURNO, "
    "aunque ya hayas hecho una acción parecida antes en la conversación. "
    "NUNCA digas que abriste, creaste o hiciste algo sin haber llamado la herramienta en este turno. "
    "\n\n"
    "FORMATO DE RESPUESTA: comunica el resultado de la herramienta usando SUS MISMAS PALABRAS, sin "
    "reformular ni resumir. Si la herramienta lista varios eventos, menciónalos TODOS con su título y hora "
    "tal como vienen. Las horas vienen en formato hablado (ej. 'cinco y media de la tarde'): "
    "repítelas EXACTAMENTE así, nunca las conviertas a números como '17:30' o '5:30'. "
    "\n\n"
    "Para CUALQUIER pregunta sobre el día, la fecha, el año o la hora, SIEMPRE debes llamar a get_datetime. "
    "NUNCA respondas la fecha, el año ni la hora de memoria: tu conocimiento del tiempo está desactualizado "
    "y siempre te equivocas. "
    "\n\n"
    "Cuando Luis te pida recordarle algo ('recuérdame', 'avísame en X minutos'), usa SIEMPRE la herramienta add_reminder. "
    "No menciones tareas ni recordatorios por iniciativa propia, solo cuando Luis te lo pida o pregunte."
)

client = AsyncClient()


async def warmup():
    stream = await client.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "Di solo: lista."},
        ],
        stream=True,
        keep_alive=KEEP_ALIVE,
        options={"num_predict": 64},
    )
    async for _ in stream:
        pass


async def stream_reply(history: list[dict]):
    """Respuesta en streaming SIN tools (se mantiene para compatibilidad)."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, *history]
    stream = await client.chat(
        model=MODEL,
        messages=messages,
        stream=True,
        keep_alive=KEEP_ALIVE,
        options={"num_predict": 150},
    )
    async for chunk in stream:
        token = chunk["message"]["content"]
        if token:
            yield token


def _limpiar_para_usuario(text: str) -> str:
    """Para salida directa: extrae el mensaje al usuario de los errores tipo
    'ERROR: ... Dile a Luis: «X»' y quita prefijos técnicos."""
    m = re.search(r"[Dd]ile a Luis:?\s*['\"«](.+?)['\"»]", text)
    if m:
        return m.group(1)
    return text.replace("ERROR:", "").strip()


async def reply_with_tools(history: list[dict], execute_tool):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, *history]

    for _ in range(5):
        response = await client.chat(
            model=MODEL,
            messages=messages,
            tools=tools.get_schemas(),
            keep_alive=KEEP_ALIVE,
            options={"num_predict": 150},
        )
        msg = response["message"]
        tool_calls = msg.get("tool_calls")

        if not tool_calls:
            content = msg.get("content", "").strip()
            # Red de seguridad: ¿el modelo escribió un tool_call como texto?
            recovered = _try_recover_toolcall(content)
            if recovered:
                name, args = recovered
                print(f"[TOOL-RECUPERADO] {name}({args})")
                result = await execute_tool(name, args)
                # Salida directa: devuelve el texto de la tool sin reformular
                if tools.is_direct_reply(name):
                    return _limpiar_para_usuario(result)
                messages.append({"role": "assistant", "content": content})
                messages.append({"role": "tool", "content": result, "name": name})
                continue
            return content

        messages.append(msg)
        direct_results = []
        for call in tool_calls:
            name = call["function"]["name"]
            args = call["function"].get("arguments", {})
            print(f"[TOOL] {name}({args})")
            result = await execute_tool(name, args)
            print(f"[TOOL] → {result}")
            messages.append({"role": "tool", "content": result, "name": name})
            if tools.is_direct_reply(name):
                direct_results.append(_limpiar_para_usuario(result))

        # Si alguna tool es de salida directa, devuelve su resultado tal cual
        # (qwen no lo reescribe: formato y veracidad garantizados).
        if direct_results:
            return " ".join(direct_results)

    return "Lo siento Luis, me enredé procesando eso."


def _try_recover_toolcall(text: str):
    """Si el modelo escribió un tool_call como JSON en el texto, lo extrae."""
    known_tools = ("open_app", "open_url", "get_time", "get_date", "add_task",
                   "list_tasks", "complete_task", "add_reminder", "list_reminders",
                   "list_calendar_events", "create_calendar_event", "get_datetime")
    if not any(t in text for t in known_tools):
        return None

    try:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            raw = match.group(0)
            raw = raw.replace('\\"', '"').replace("\\'", "'")
            raw = re.sub(r'(\w+)=', r'"\1":', raw)
            raw = raw.replace("'", '"')
            raw = re.sub(r'""+', '"', raw)
            data = _json.loads(raw)
            name = data.get("name")
            args = data.get("parameters") or data.get("arguments") or {}
            if name in known_tools:
                return name, args
    except Exception:
        pass

    name_match = re.search(r'"?name"?\s*[:=]\s*"?(\w+)"?', text)
    if name_match:
        name = name_match.group(1)
        if name in known_tools:
            args = {}
            for key in ("title", "site", "name", "text", "when"):
                m = re.search(rf'"?{key}"?\s*[:=]\s*"([^"]+)"', text)
                if m:
                    args[key] = m.group(1)
            return name, args
    sin_args = ("list_tasks", "list_reminders", "list_calendar_events",
                "get_time", "get_date", "get_datetime")
    for tool_name in sin_args:
        if tool_name in text:
            return tool_name, {}
    return None