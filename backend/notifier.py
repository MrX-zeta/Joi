import asyncio
from datetime import datetime
import db


async def reminder_loop(push):
    """
    Revisa cada 20s si hay recordatorios vencidos.
    `push` es una corutina que envía el evento a los clientes conectados.
    """
    while True:
        try:
            due = await asyncio.to_thread(db.due_reminders, datetime.now())
            for r in due:
                await push(r["id"], r["text"])
                await asyncio.to_thread(db.mark_reminder_notified, r["id"])
        except Exception as e:
            print(f"[NOTIFIER] error: {e!r}")
        await asyncio.sleep(20)