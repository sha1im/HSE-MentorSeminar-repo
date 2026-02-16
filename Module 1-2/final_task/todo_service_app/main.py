from typing import Optional, List

from fastapi import FastAPI, HTTPException, Query

from todo_service_app.db import init_db, get_conn
from todo_service_app.schemas import ItemCreate, ItemUpdate, ItemOut

app = FastAPI(title="TODO Service")


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.post("/items", response_model=ItemOut)
def create_item(payload: ItemCreate) -> ItemOut:
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO items (title, description, priority, completed, archived)
            VALUES (?, ?, ?, 0, 0)
            """,
            (payload.title, payload.description, payload.priority),
        )
        conn.commit()

        item_id = cur.lastrowid
        row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()

    return _row_to_item(row)


@app.get("/items", response_model=List[ItemOut])
def list_items(
    query: Optional[str] = Query(default=None, description="Search by title substring"),
) -> List[ItemOut]:
    sql = "SELECT * FROM items WHERE archived = 0"
    params = []

    if query:
        sql += " AND title LIKE ?"
        params.append(f"%{query}%")

    sql += " ORDER BY priority DESC, id DESC"

    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()

    return [_row_to_item(r) for r in rows]


@app.get("/items/{item_id}", response_model=ItemOut)
def get_item(item_id: int) -> ItemOut:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Item not found")

    return _row_to_item(row)


@app.patch("/items/{item_id}", response_model=ItemOut)
def update_item(item_id: int, payload: ItemUpdate) -> ItemOut:
    updates = []
    params = []

    if payload.title is not None:
        updates.append("title = ?")
        params.append(payload.title)

    if payload.description is not None:
        updates.append("description = ?")
        params.append(payload.description)

    if payload.priority is not None:
        updates.append("priority = ?")
        params.append(payload.priority)

    if payload.completed is not None:
        updates.append("completed = ?")
        params.append(1 if payload.completed else 0)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    params.append(item_id)

    with get_conn() as conn:
        exists = conn.execute("SELECT id FROM items WHERE id = ?", (item_id,)).fetchone()
        if exists is None:
            raise HTTPException(status_code=404, detail="Item not found")

        conn.execute(
            f"UPDATE items SET {', '.join(updates)} WHERE id = ?",
            params,
        )
        conn.commit()

        row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()

    return _row_to_item(row)


@app.delete("/items/{item_id}")
def archive_item(item_id: int):
    with get_conn() as conn:
        exists = conn.execute("SELECT id FROM items WHERE id = ?", (item_id,)).fetchone()
        if exists is None:
            raise HTTPException(status_code=404, detail="Item not found")

        # Вместо удаления — архивируем
        conn.execute("UPDATE items SET archived = 1 WHERE id = ?", (item_id,))
        conn.commit()

    return {"status": "archived", "id": item_id}

def _row_to_item(row) -> ItemOut:
    return ItemOut(
        id=row["id"],
        title=row["title"],
        description=row["description"],
        priority=row["priority"],
        completed=bool(row["completed"]),
        archived=bool(row["archived"]),
        created_at=row["created_at"],
    )