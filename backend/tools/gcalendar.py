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
