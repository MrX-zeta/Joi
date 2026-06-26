from datetime import datetime, timedelta
from googleapiclient.discovery import build
from .system import _hora_12h
from gauth import get_credentials

DIAS_SEM = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
         "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def list_calendar_events(**kwargs) -> str:
    """Lee los próximos eventos del calendario de Luis (próximos 7 días)."""
    try:
        creds = get_credentials()
        service = build("calendar", "v3", credentials=creds)

        now = datetime.utcnow()
        fin = now + timedelta(days=7)

        result = service.events().list(
            calendarId="primary",
            timeMin=now.isoformat() + "Z",
            timeMax=fin.isoformat() + "Z",
            singleEvents=True,
            orderBy="startTime",
            maxResults=10,
        ).execute()

        eventos = result.get("items", [])
        if not eventos:
            return "No tienes eventos próximos en el calendario."

        lineas = []
        for ev in eventos:
            inicio = ev["start"].get("dateTime", ev["start"].get("date"))
            titulo = ev.get("summary", "(sin título)")
            try:
                dt = datetime.fromisoformat(inicio.replace("Z", "+00:00"))
                dia_sem = DIAS_SEM[dt.weekday()]
                cuando = f"el {dia_sem} {dt.day} de {MESES[dt.month-1]} a las {_hora_12h(dt)}"
            except Exception:
                cuando = inicio
            lineas.append(f"{titulo} {cuando}")
        return "Tus próximos eventos: " + "; ".join(lineas) + "."
    except Exception as e:
        return f"No pude leer el calendario: {e}"


def create_calendar_event(title: str = "", day: str = "", start_time: str = "",
                          end_time: str = "", duration_min: int = 60, **kwargs) -> str:
    """Crea un evento. Recibe día y horas por separado (no texto libre)."""
    import dateparser
    title = title.strip()
    if not title or not day or not start_time:
        return "ERROR: faltan datos. Dile a Luis: 'Necesito el título, el día y la hora.'"

    settings = {"PREFER_DATES_FROM": "future", "RELATIVE_BASE": datetime.now()}

    # Limpia prefijos que confunden a dateparser ("este domingo" → "domingo")
    day_limpio = (day.lower()
                  .replace("este ", "").replace("esta ", "")
                  .replace("el ", "").replace("la ", "")
                  .replace("próximo ", "").replace("próxima ", "")
                  .strip())

    inicio = dateparser.parse(f"{day_limpio} {start_time}", languages=["es"], settings=settings)
    if not inicio:
        return "ERROR: no se creó el evento. Dile a Luis: 'No entendí la fecha, ¿me la repites?'"

    # Hora de fin: si se dio, úsala; si no, duración default
    fin = None
    if end_time.strip():
        fin_parsed = dateparser.parse(f"{day_limpio} {end_time}", languages=["es"], settings=settings)
        if fin_parsed:
            fin = inicio.replace(hour=fin_parsed.hour, minute=fin_parsed.minute)
            if fin <= inicio:
                fin = None
    if not fin:
        fin = inicio + timedelta(minutes=int(duration_min or 60))

    try:
        creds = get_credentials()
        service = build("calendar", "v3", credentials=creds)
        evento = {
            "summary": title,
            "start": {"dateTime": inicio.isoformat(), "timeZone": "America/Mexico_City"},
            "end": {"dateTime": fin.isoformat(), "timeZone": "America/Mexico_City"},
        }
        service.events().insert(calendarId="primary", body=evento).execute()
        dia_sem = DIAS_SEM[inicio.weekday()]
        ini_str = f"el {dia_sem} {inicio.day} de {MESES[inicio.month-1]} a las {_hora_12h(inicio)}"
        fin_str = _hora_12h(fin)
        return f"Listo, creé el evento {title} {ini_str}, hasta las {fin_str}."
    except Exception as e:
        return f"No pude crear el evento: {e}"