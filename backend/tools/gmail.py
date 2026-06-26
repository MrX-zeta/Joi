import re
from googleapiclient.discovery import build

from gauth import get_credentials


def _nombre_remitente(from_header: str) -> str:
    """'Juan Pérez <juan@x.com>' → 'Juan Pérez'; 'juan@x.com' → 'juan@x.com'."""
    m = re.match(r'\s*"?([^"<]+?)"?\s*<', from_header)
    if m:
        return m.group(1).strip()
    return from_header.strip()


def revisar_correo(query: str = "", **kwargs) -> str:
    """Revisa el correo: sin query lee no leídos; con query busca por remitente/tema."""
    query = query.strip()
    try:
        creds = get_credentials()
        service = build("gmail", "v1", credentials=creds)

        if query:
            result = service.users().messages().list(
                userId="me", q=query, maxResults=5
            ).execute()
        else:
            result = service.users().messages().list(
                userId="me", labelIds=["INBOX", "UNREAD"], maxResults=5
            ).execute()

        mensajes = result.get("messages", [])
        if not mensajes:
            return f"No encontré correos sobre {query}." if query else "No tienes correos sin leer."

        lineas = []
        for m in mensajes:
            msg = service.users().messages().get(
                userId="me", id=m["id"], format="metadata",
                metadataHeaders=["From", "Subject"],
            ).execute()
            headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
            remitente = _nombre_remitente(headers.get("From", "alguien"))
            asunto = headers.get("Subject", "(sin asunto)")
            lineas.append(f"de {remitente}, asunto: {asunto}")

        if query:
            return f"Correos sobre {query}: " + "; ".join(lineas) + "."
        return "Tus correos sin leer más recientes: " + "; ".join(lineas) + "."
    except Exception as e:
        return f"No pude revisar el correo: {e}"