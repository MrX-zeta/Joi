import dateparser
from datetime import datetime, timedelta
import db

DIAS_EXPLICITOS = ["mañana", "pasado mañana", "lunes", "martes", "miércoles",
                   "jueves", "viernes", "sábado", "domingo", "/", "-",
                   "enero", "febrero", "marzo", "abril", "mayo", "junio",
                   "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

RELATIVAS = ["minuto", "hora", "segundo"]

def add_reminder(text: str = "", when: str = "", **kwargs) -> str:
    """Crea un recordatorio. 'when' es una expresión de tiempo en español."""
    from .system import _hora_12h
    text = text.strip()
    when = when.strip()

    if not text:
        return "¿Qué quieres que te recuerde?"
    if not when:
        return "¿A qué hora o en cuánto tiempo te lo recuerdo?"

    now = datetime.now()
    when_low = when.lower()

    menciona_otro_dia = any(d in when_low for d in DIAS_EXPLICITOS)
    es_relativa = any(r in when_low for r in RELATIVAS)

    parsed = dateparser.parse(
        when,
        languages=["es"],
        settings={"PREFER_DATES_FROM": "future", "RELATIVE_BASE": now},
    )

    # Blindaje: si no se pudo interpretar, error claro sin agendar nada
    if not parsed:
        return ("No entendí cuándo. Dime una hora como «a las 5», "
                "un tiempo como «en 10 minutos», o un día como «mañana a las 3».")

    try:
        if es_relativa:
            remind_at = parsed
        elif menciona_otro_dia:
            remind_at = parsed
        else:
            # Hora suelta: estrictamente hoy, próxima ocurrencia (am o pm)
            h, m = parsed.hour, parsed.minute
            cand_am = now.replace(hour=h % 12, minute=m, second=0, microsecond=0)
            cand_pm = now.replace(hour=(h % 12) + 12, minute=m, second=0, microsecond=0)
            opciones = sorted([c for c in (cand_am, cand_pm) if c > now])
            if not opciones:
                return ("Esa hora ya pasó hoy. Dime una hora más tarde "
                        "o especifica el día, por ejemplo «mañana a las 8».")
            remind_at = opciones[0]
    except Exception:
        return "No pude calcular esa hora. Intenta con «a las 5» o «en 10 minutos»."

    # Blindaje final: nunca agendar en el pasado
    if remind_at <= now:
        return "Esa hora ya pasó. Dime una hora futura."

    # Blindaje: límite razonable (no más de 1 año adelante)
    if (remind_at - now).days > 365:
        return "Eso es demasiado lejano. Dime una fecha dentro del próximo año."

    db.add_reminder(text, remind_at)

    # Formato hablado: sin fecha si es hoy, con fecha si es otro día
    hora_str = _hora_12h(remind_at)
    if remind_at.date() == now.date():
        cuando = f"a las {hora_str}"
    else:
        MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
                 "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        cuando = f"el {remind_at.day} de {MESES[remind_at.month-1]} a las {hora_str}"
    return f"Listo, te recordaré {text} {cuando}."


def list_reminders(**kwargs) -> str:
    """Lista los recordatorios pendientes."""
    from .system import _hora_12h
    rems = db.list_reminders(include_notified=False)
    if not rems:
        return "No tienes recordatorios pendientes."

    now = datetime.now()
    MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
             "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    lineas = []
    for r in rems:
        dt = datetime.fromisoformat(r["remind_at"])
        hora_str = _hora_12h(dt)
        if dt.date() == now.date():
            cuando = f"a las {hora_str}"
        else:
            cuando = f"el {dt.day} de {MESES[dt.month-1]} a las {hora_str}"
        lineas.append(f"{r['text']} {cuando}")
    return "Tus recordatorios: " + "; ".join(lineas) + "."