from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field


# -----------------------------
# Models (schemas)
# -----------------------------
class TaskStatus(str, Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=2000)
    due_date: Optional[datetime] = None
    status: TaskStatus = TaskStatus.todo


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=2000)
    due_date: Optional[datetime] = None
    status: Optional[TaskStatus] = None


class Task(TaskCreate):
    id: str
    created_at: datetime
    updated_at: datetime


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None


# -----------------------------
# App + In-memory storage
# -----------------------------
app = FastAPI(
    title="Task Tracker MVP API",
    version="0.1.0",
    description="Hackathon-ready minimal Task Tracker API (in-memory).",
)

DB: Dict[str, Task] = {}


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


# -----------------------------
# Health
# -----------------------------
@app.get("/")
def root():
    return {
        "service": "Intelligent Assistant API",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
def health():
    return {"status": "ok", "time": now_utc().isoformat()}


# -----------------------------
# CRUD: Tasks
# -----------------------------
@app.post("/tasks", response_model=Task, responses={400: {"model": ErrorResponse}})
def create_task(payload: TaskCreate):
    task_id = str(uuid4())
    ts = now_utc()
    task = Task(id=task_id, created_at=ts, updated_at=ts, **payload.model_dump())
    DB[task_id] = task
    return task


@app.get("/tasks", response_model=List[Task])
def list_tasks(
    status: Optional[TaskStatus] = Query(default=None),
    q: Optional[str] = Query(default=None, description="Search in title/description"),
):
    items = list(DB.values())

    if status:
        items = [t for t in items if t.status == status]

    if q:
        ql = q.lower()
        items = [
            t
            for t in items
            if ql in t.title.lower() or (t.description and ql in t.description.lower())
        ]

    # newest first
    items.sort(key=lambda t: t.created_at, reverse=True)
    return items


@app.get("/tasks/{task_id}", response_model=Task, responses={404: {"model": ErrorResponse}})
def get_task(task_id: str):
    task = DB.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.patch("/tasks/{task_id}", response_model=Task, responses={404: {"model": ErrorResponse}})
def update_task(task_id: str, payload: TaskUpdate):
    task = DB.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    data = payload.model_dump(exclude_unset=True)
    updated = task.model_copy(update=data)
    updated.updated_at = now_utc()
    DB[task_id] = updated
    return updated


@app.delete("/tasks/{task_id}", responses={204: {"description": "Deleted"}, 404: {"model": ErrorResponse}})
def delete_task(task_id: str):
    if task_id not in DB:
        raise HTTPException(status_code=404, detail="Task not found")
    del DB[task_id]
    return None  # FastAPI will return 200 by default unless we force status_code via decorator


# Optional: explicit 204 version (cleaner)
@app.delete("/tasks/{task_id}/hard", status_code=204, responses={404: {"model": ErrorResponse}})
def delete_task_204(task_id: str):
    if task_id not in DB:
        raise HTTPException(status_code=404, detail="Task not found")
    del DB[task_id]
    return