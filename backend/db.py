import sqlite3
import threading
from datetime import datetime, date
from pathlib import Path

DB_PATH = Path(__file__).parent / "joi.db"
_lock = threading.Lock()


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c


def init_db() -> None:
    with _lock, _conn() as c:
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                role       TEXT NOT NULL,
                content    TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        c.execute("CREATE INDEX IF NOT EXISTS idx_messages_date ON messages(created_at)")


def insert_message(role: str, content: str) -> None:
    with _lock, _conn() as c:
        c.execute(
            "INSERT INTO messages (role, content, created_at) VALUES (?, ?, ?)",
            (role, content, datetime.now().isoformat()),
        )


def get_today() -> list[dict]:
    today = date.today().isoformat()
    with _lock, _conn() as c:
        rows = c.execute(
            "SELECT role, content FROM messages WHERE created_at >= ? ORDER BY id ASC",
            (today,),
        ).fetchall()
    return [{"role": r["role"], "content": r["content"]} for r in rows]


def get_recent(limit: int = 20) -> list[dict]:
    """Últimos N turnos (para precargar la memoria de Ollama al arrancar)."""
    with _lock, _conn() as c:
        rows = c.execute(
            "SELECT role, content FROM messages ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]