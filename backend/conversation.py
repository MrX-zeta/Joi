MAX_TURNS = 20

_history: list[dict] = []


def append(role: str, content: str) -> None:
    _history.append({"role": role, "content": content})
    if len(_history) > MAX_TURNS:
        del _history[: len(_history) - MAX_TURNS]


def drop_last() -> None:
    if _history:
        _history.pop()


def messages() -> list[dict]:
    return list(_history)