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
    cuando = remind_at.strftime("%H:%M del %d/%m")
    return f"Listo, te recordaré «{text}» a las {cuando}."


def list_reminders(**kwargs) -> str:
    """Lista los recordatorios pendientes."""
    rems = db.list_reminders(include_notified=False)
    if not rems:
        return "No tienes recordatorios pendientes."
    lineas = []
    for r in rems:
        hora = datetime.fromisoformat(r["remind_at"]).strftime("%H:%M")
        lineas.append(f"{r['text']} a las {hora}")
    return "Tus recordatorios: " + "; ".join(lineas) + "."