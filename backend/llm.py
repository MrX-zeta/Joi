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
    "Comunica el resultado de la herramienta usando sus mismas palabras, sin reformular. "
    "\n\n"
    "No menciones tareas ni recordatorios salvo que Luis pregunte por ellos."
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
                messages.append({"role": "assistant", "content": content})
                messages.append({"role": "tool", "content": result, "name": name})
                continue  # vuelve a pedir para que redacte la respuesta final
            return content

        messages.append(msg)
        for call in tool_calls:
            name = call["function"]["name"]
            args = call["function"].get("arguments", {})
            print(f"[TOOL] {name}({args})")
            result = await execute_tool(name, args)
            print(f"[TOOL] → {result}")
            messages.append({"role": "tool", "content": result, "name": name})

    return "Lo siento Luis, me enredé procesando eso."

def _try_recover_toolcall(text: str):
    """Si el modelo escribió un tool_call como JSON en el texto, lo extrae."""
    known_tools = ("open_app", "open_url", "get_time", "get_date", "add_task",
                   "list_tasks", "complete_task", "add_reminder", "list_reminders",
                   "list_calendar_events", "create_calendar_event")
    if not any(t in text for t in known_tools):
        return None

    # Intento 1: parsear como JSON (reparando errores comunes)
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

    # Intento 2 (fallback): si el JSON está muy roto, extrae el nombre con regex.
    # Para tools sin argumentos (list_*, get_*) esto basta.
    name_match = re.search(r'"?name"?\s*[:=]\s*"?(\w+)"?', text)
    if name_match:
        name = name_match.group(1)
        if name in known_tools:
            # Intenta extraer args simples tipo "title": "valor"
            args = {}
            for key in ("title", "site", "name", "text", "when"):
                m = re.search(rf'"?{key}"?\s*[:=]\s*"([^"]+)"', text)
                if m:
                    args[key] = m.group(1)
            return name, args
    sin_args = ("list_tasks", "list_reminders", "list_calendar_events",
                "get_time", "get_date")
    for tool_name in sin_args:
        if tool_name in text:
            return tool_name, {}
    return None