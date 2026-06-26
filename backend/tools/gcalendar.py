from datetime import datetime, timedelta
from googleapiclient.discovery import build

from gauth import get_credentials


def list_calendar_events(**kwargs) -> str:
    """Lee los próximos eventos del calendario de Luis (hoy y mañana)."""
    try:
        creds = get_credentials()
        service = build("calendar", "v3", credentials=creds)

        now = datetime.utcnow()
        fin = now + timedelta(days=2)

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
                cuando = dt.strftime("%d/%m a las %H:%M")
            except Exception:
                cuando = inicio
            lineas.append(f"{titulo} el {cuando}")
        return "Tus próximos eventos: " + "; ".join(lineas) + "."
    except Exception as e:
        return f"No pude leer el calendario: {e}"

def create_calendar_event(title: str = "", when: str = "", duration_min: int = 60, **kwargs) -> str:
    """Crea un evento en el calendario de Luis."""
    import dateparser
    import re
    title = title.strip()
    if not title or not when:
        return "Necesito el título del evento y cuándo."

    w = when.lower().strip()
    base = datetime.now()
    settings = {"PREFER_DATES_FROM": "future", "RELATIVE_BASE": base}

    # Separa inicio y fin si hay un rango ("hasta", "-", "de X a Y", o segundo "a las")
    fin_texto = None
    if " hasta " in w:
        ini_texto, fin_texto = w.split(" hasta ", 1)
    elif re.search(r'\bde\s+[\d:]+\s*(?:am|pm)?\s+a\s+[\d:]+', w):
        # patrón "de 11:30 a 14:00" / "de 11:30am a 2pm"
        m = re.search(
            r'(.*?)\bde\s+([\d:]+\s*(?:am|pm)?)\s+a\s+([\d:]+\s*(?:am|pm)?)',
            w,
        )
        if m:
            prefijo = m.group(1).strip()      # "domingo"
            hora_ini = m.group(2).strip()     # "11:30"
            hora_fin = m.group(3).strip()     # "14:00"
            ini_texto = f"{prefijo} {hora_ini}".strip()
            fin_texto = hora_fin
        else:
            ini_texto = w
    elif "-" in w:
        ini_texto, fin_texto = w.split("-", 1)
    else:
        partes = w.split(" a las ")
        if len(partes) > 2:
            ini_texto = " a las ".join(partes[:2])
            fin_texto = partes[2]
        else:
            ini_texto = w

    inicio = dateparser.parse(ini_texto, languages=["es"], settings=settings)
    if not inicio:
        return "ERROR: no se creó el evento. Dile a Luis exactamente: 'No entendí la hora, ¿me la repites?'"

    # Calcula el fin: desde la hora de fin si se dio, si no por duración
    fin = None
    if fin_texto:
        fin_settings = {"PREFER_DATES_FROM": "future", "RELATIVE_BASE": inicio}
        fin_parsed = dateparser.parse(fin_texto, languages=["es"], settings=fin_settings)
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
        ini_str = inicio.strftime("%d/%m a las %H:%M")
        fin_str = fin.strftime("%H:%M")
        return f"Listo, creé el evento «{title}» el {ini_str}, hasta las {fin_str}."
    except Exception as e:
        return f"No pude crear el evento: {e}"