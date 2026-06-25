import db


def add_task(title: str = "", **kwargs) -> str:
    """Guarda una nueva tarea."""
    title = title.strip()
    if not title:
        return "No entendí qué tarea anotar."
    task_id = db.add_task(title)
    return f"Anotado: «{title}»."


def list_tasks(**kwargs) -> str:
    """Lista las tareas pendientes."""
    tasks = db.list_tasks(include_done=False)
    if not tasks:
        return "No tienes tareas pendientes."
    lineas = [f"{i+1}. {t['title']}" for i, t in enumerate(tasks)]
    return "Tus tareas pendientes son: " + "; ".join(lineas) + "."


def complete_task(title: str = "", **kwargs) -> str:
    """Marca una tarea como completada, buscándola por su texto."""
    title = title.strip().lower()
    if not title:
        return "¿Cuál tarea completaste?"
    tasks = db.list_tasks(include_done=False)
    # Busca la tarea cuyo título más se parezca
    from difflib import SequenceMatcher
    best = None
    best_score = 0.0
    for t in tasks:
        score = SequenceMatcher(None, title, t["title"].lower()).ratio()
        if title in t["title"].lower():
            score = 1.0
        if score > best_score:
            best_score = score
            best = t
    if best and best_score > 0.5:
        db.complete_task(best["id"])
        return f"Marqué como hecha: «{best['title']}»."
    return f"No encontré una tarea que coincida con «{title}»."