from datetime import datetime, date
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from models import Base, Message, Task, Reminder

DB_PATH = Path(__file__).parent / "joi.db"
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine, expire_on_commit=False)


def init_db() -> None:
    # Las tablas ya las gestiona Alembic; create_all es respaldo idempotente.
    Base.metadata.create_all(engine)


# ---------- Mensajes (historial) ----------

def insert_message(role: str, content: str) -> None:
    with Session() as s:
        s.add(Message(role=role, content=content, created_at=datetime.now()))
        s.commit()


def get_today() -> list[dict]:
    start = datetime.combine(date.today(), datetime.min.time())
    with Session() as s:
        rows = s.execute(
            select(Message).where(Message.created_at >= start).order_by(Message.id.asc())
        ).scalars().all()
    return [{"role": r.role, "content": r.content} for r in rows]


def get_recent(limit: int = 20) -> list[dict]:
    """Últimos N turnos (para precargar la memoria de Ollama al arrancar)."""
    with Session() as s:
        rows = s.execute(
            select(Message).order_by(Message.id.desc()).limit(limit)
        ).scalars().all()
    return [{"role": r.role, "content": r.content} for r in reversed(rows)]


# ---------- Tareas ----------

def add_task(title: str) -> int:
    with Session() as s:
        t = Task(title=title, done=False, created_at=datetime.now())
        s.add(t)
        s.commit()
        return t.id


def list_tasks(include_done: bool = False) -> list[dict]:
    with Session() as s:
        stmt = select(Task).order_by(Task.id.asc())
        if not include_done:
            stmt = stmt.where(Task.done == False)  # noqa: E712
        rows = s.execute(stmt).scalars().all()
    return [{"id": t.id, "title": t.title, "done": t.done} for t in rows]


def complete_task(task_id: int) -> bool:
    with Session() as s:
        t = s.get(Task, task_id)
        if not t:
            return False
        t.done = True
        s.commit()
        return True


# ---------- Recordatorios ----------

def add_reminder(text: str, remind_at: datetime) -> int:
    with Session() as s:
        r = Reminder(text=text, remind_at=remind_at, notified=False, created_at=datetime.now())
        s.add(r)
        s.commit()
        return r.id


def list_reminders(include_notified: bool = False) -> list[dict]:
    with Session() as s:
        stmt = select(Reminder).order_by(Reminder.remind_at.asc())
        if not include_notified:
            stmt = stmt.where(Reminder.notified == False)  # noqa: E712
        rows = s.execute(stmt).scalars().all()
    return [{"id": r.id, "text": r.text, "remind_at": r.remind_at.isoformat()} for r in rows]


def due_reminders(now: datetime | None = None) -> list[dict]:
    """Recordatorios cuya hora ya llegó y no se han notificado."""
    now = now or datetime.now()
    with Session() as s:
        rows = s.execute(
            select(Reminder).where(
                Reminder.notified == False,  # noqa: E712
                Reminder.remind_at <= now,
            ).order_by(Reminder.remind_at.asc())
        ).scalars().all()
    return [{"id": r.id, "text": r.text} for r in rows]


def mark_reminder_notified(reminder_id: int) -> None:
    with Session() as s:
        r = s.get(Reminder, reminder_id)
        if r:
            r.notified = True
            s.commit()