from ollama import AsyncClient
import tools
import json as _json
import re

MODEL = "llama3.2:3b"
KEEP_ALIVE = -1

SYSTEM_PROMPT = (
    "Eres Joi, la asistente personal de Luis. "
    "Te diriges a él por su nombre, Luis. "
    "Personalidad femenina, cálida, cercana y directa. "
    "REGLA CLAVE DE BREVEDAD: respondes en 1 o 2 frases cortas, como en una conversación hablada natural. "
    "Vas directo al punto, sin rodeos, sin preámbulos, sin listas. "
    "Solo te extiendes más si Luis te pide explícitamente que profundices o expliques en detalle. "
    "Hablas siempre en español correcto y natural. "
    "Tienes herramientas disponibles: úsalas cuando Luis pida algo que requiera datos actuales "
    "como la hora o la fecha. No inventes esos datos, usa la herramienta. "
    "IMPORTANTE: cuando una herramienta te dé un resultado, DEBES comunicar ese dato exacto a Luis "
    "en tu respuesta. Por ejemplo, si la herramienta dice la fecha, dísela claramente."
    "Nunca escribas llamadas a herramientas como texto JSON en tu respuesta. "
    "Usa las herramientas through el mecanismo correcto, y responde solo con lenguaje natural."
    "Ejecuta SOLO la acción que Luis pide en su último mensaje. "
    "NUNCA repitas acciones de mensajes anteriores de la conversación."
    "No menciones tareas, pendientes ni recordatorios a menos que Luis pregunte explícitamente por ellos. "
    "Si Luis habla de otro tema, responde solo a ese tema sin recordarle sus pendientes."
    "IMPORTANTE: cuando una herramienta te dé un resultado, comunica ese resultado a Luis "
    "usando exactamente las mismas palabras que devolvió la herramienta, sin reformular ni inventar palabras. "
    "Por ejemplo, si la herramienta dice 'Listo, te recordaré tomar agua a las 16:15', repite eso tal cual."
    "Háblale SIEMPRE a Luis directamente, en segunda persona ('tú', 'tienes', 'tu reunión'), "
    "nunca en tercera persona. Di 'Tienes una reunión' en vez de 'Luis tiene una reunión'."
    "REGLA CRÍTICA: NUNCA inventes información. No inventes eventos, reuniones, tareas, horas ni fechas. "
    "Si no tienes el dato de una herramienta, di que no tienes esa información. "
    "Solo menciona eventos o tareas que una herramienta te haya devuelto explícitamente en esta conversación. "
    "Si la herramienta de calendario no devolvió eventos, di que no hay eventos, nunca inventes uno."
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
                   "list_calendar_events")
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