import db

MAX_TURNS = 20

_history: list[dict] = []


def load_from_db() -> None:
    """Precarga la memoria de Ollama con los últimos turnos guardados."""
    global _history
    _history = db.get_recent(MAX_TURNS)


def append(role: str, content: str) -> None:
    _history.append({"role": role, "content": content})
    if len(_history) > MAX_TURNS:
        del _history[: len(_history) - MAX_TURNS]
    db.insert_message(role, content)


def drop_last() -> None:
    """Quita el último turno de la memoria en RAM (no de la DB)."""
    if _history:
        _history.pop()


def messages() -> list[dict]:
    return list(_history)