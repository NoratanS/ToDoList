from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import uuid4
from datetime import datetime, timedelta

app = FastAPI()


# Classes
class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=300)
    status: str = Field("TODO", pattern="^(TODO|IN_PROGRESS|DONE)$")


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=300)


class PomodoroSession(BaseModel):
    task_id: str
    start_time: datetime
    end_time: datetime
    completed: bool = False


# Mock Data
tasks = []
pomodoro_sessions = []


# Methods
@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI ToDo and Pomodoro app!"}


@app.post("/tasks", response_model=Task)
def create_task(task: TaskCreate):
    if any(t.title == task.title for t in tasks):
        raise HTTPException(status_code=400, detail="Task already exists")

    new_task = Task(
        title=task.title,
        description=task.description,
        status="TODO"
    )
    tasks.append(new_task)
    return new_task


@app.get("/tasks", response_model=List[Task])
def get_tasks(status: Optional[str] = None):
    if status:
        return [task for task in tasks if task.status == status]
    return tasks


@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: str):
    for task in tasks:
        if task.id == task_id:
            return task
    raise HTTPException(status_code=404, detail="Task not found")


@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: str, task: TaskCreate):
    for t in tasks:
        if t.id == task_id:
            if any(other.title == task.title and other.id != task.id for other in tasks):
                raise HTTPException(status_code=400, detail="Task title must be unique")
            t.title = task.title
            t.description = task.description
            return t
    raise HTTPException(status_code=404, detail="Task not found")


@app.delete("/tasks/{task_id}")
def delete_task(task_id: str):
    global tasks
    tasks = [task for task in tasks if task.id != task_id]
    return {"message": "Task deleted"}


@app.post("/pomodoro", response_model=PomodoroSession)
def create_pomodoro(task_id: str):
    for task in tasks:
        if task.id == task_id:
            if any(session.task_id == task.id and not session.completed for session in pomodoro_sessions):
                raise HTTPException(status_code=400, detail="Active Pomodoro session already exists for this task")
            new_session = PomodoroSession(
                task_id=task.id,
                start_time=datetime.now(),
                end_time=datetime.now() + timedelta(minutes=25),
                completed=False
            )
            pomodoro_sessions.append(new_session)
            return new_session
    raise HTTPException(status_code=404, detail="Task not found")


@app.post("/pomodoro/{task_id}/stop")
def stop_pomodoro(task_id: str):
    for session in pomodoro_sessions:
        if session.task_id == task_id and not session.completed:
            session.completed = True
            return {"message": "Pomodoro session stopped"}
    raise HTTPException(status_code=404, detail="No active Pomodoro session found for this task")


@app.get("/pomodoro/stats")
def get_pomodoro_stats():
    stats = {}
    for session in pomodoro_sessions:
        if session.completed:
            stats[session.task_id] = stats.get(session.task_id, 0) + 1
    return {
        "completed_sessions": stats,
        "total_time_spent": sum(
            (session.end_time - session.start_time).total_seconds() for session in pomodoro_sessions if
            session.completed)
    }
