from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, Date, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from pydantic import BaseModel
from typing import List
from datetime import date, datetime, timedelta

# Database Configuration
DATABASE_URL = "sqlite:///./schoolplanner.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Models
class Timetable(Base):
    __tablename__ = 'timetables'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    tasks = relationship("Task", back_populates="timetable")

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    due_date = Column(Date)
    completed = Column(Boolean, default=False)
    timetable_id = Column(Integer, ForeignKey('timetables.id'))
    timetable = relationship("Timetable", back_populates="tasks")

Base.metadata.create_all(bind=engine)

# Schemas
class TimetableCreate(BaseModel):
    name: str

class TimetableResponse(BaseModel):
    id: int
    name: str

class TaskCreate(BaseModel):
    title: str
    description: str
    due_date: date

class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    due_date: date
    completed: bool

# Initialize FastAPI
app = FastAPI()

# Timetable Endpoints

@app.post("/timetable/create", response_model=TimetableResponse)
def create_timetable(timetable: TimetableCreate, db: Session = Depends(get_db)):
    new_timetable = Timetable(name=timetable.name)
    db.add(new_timetable)
    db.commit()
    db.refresh(new_timetable)
    return new_timetable

@app.get("/timetable/view", response_model=List[TimetableResponse])
def view_timetables(db: Session = Depends(get_db)):
    timetables = db.query(Timetable).all()
    return timetables

@app.get("/timetable/{timetable_id}", response_model=TimetableResponse)
def get_timetable(timetable_id: int, db: Session = Depends(get_db)):
    timetable = db.query(Timetable).filter(Timetable.id == timetable_id).first()
    if not timetable:
        raise HTTPException(status_code=404, detail="Timetable not found")
    return timetable

@app.put("/timetable/{timetable_id}", response_model=TimetableResponse)
def update_timetable(timetable_id: int, timetable: TimetableCreate, db: Session = Depends(get_db)):
    existing_timetable = db.query(Timetable).filter(Timetable.id == timetable_id).first()
    if not existing_timetable:
        raise HTTPException(status_code=404, detail="Timetable not found")
    existing_timetable.name = timetable.name
    db.commit()
    db.refresh(existing_timetable)
    return existing_timetable

@app.delete("/timetable/{timetable_id}")
def delete_timetable(timetable_id: int, db: Session = Depends(get_db)):
    timetable = db.query(Timetable).filter(Timetable.id == timetable_id).first()
    if not timetable:
        raise HTTPException(status_code=404, detail="Timetable not found")
    db.delete(timetable)
    db.commit()
    return {"detail": "Timetable deleted"}

# Task Endpoints

@app.post("/task/create", response_model=TaskResponse)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    new_task = Task(title=task.title, description=task.description, due_date=task.due_date)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

@app.get("/task/view", response_model=List[TaskResponse])
def view_tasks(db: Session = Depends(get_db)):
    tasks = db.query(Task).all()
    return tasks

@app.get("/task/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.put("/task/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task: TaskCreate, db: Session = Depends(get_db)):
    existing_task = db.query(Task).filter(Task.id == task_id).first()
    if not existing_task:
        raise HTTPException(status_code=404, detail="Task not found")
    existing_task.title = task.title
    existing_task.description = task.description
    existing_task.due_date = task.due_date
    db.commit()
    db.refresh(existing_task)
    return existing_task

@app.delete("/task/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return {"detail": "Task deleted"}

@app.patch("/task/{task_id}/complete", response_model=TaskResponse)
def mark_task_complete(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.completed = True
    db.commit()
    db.refresh(task)
    return task

@app.get("/task/completed", response_model=List[TaskResponse])
def view_completed_tasks(db: Session = Depends(get_db)):
    tasks = db.query(Task).filter(Task.completed == True).all()
    return tasks

@app.get("/task/pending", response_model=List[TaskResponse])
def view_pending_tasks(db: Session = Depends(get_db)):
    tasks = db.query(Task).filter(Task.completed == False).all()
    return tasks

# Task and Timetable Associations

@app.get("/timetable/{timetable_id}/tasks", response_model=List[TaskResponse])
def view_tasks_in_timetable(timetable_id: int, db: Session = Depends(get_db)):
    tasks = db.query(Task).filter(Task.timetable_id == timetable_id).all()
    return tasks

@app.post("/timetable/{timetable_id}/task", response_model=TaskResponse)
def add_task_to_timetable(timetable_id: int, task: TaskCreate, db: Session = Depends(get_db)):
    new_task = Task(title=task.title, description=task.description, due_date=task.due_date, timetable_id=timetable_id)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

@app.delete("/timetable/{timetable_id}/task/{task_id}")
def remove_task_from_timetable(timetable_id: int, task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id, Task.timetable_id == timetable_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found in the timetable")
    db.delete(task)
    db.commit()
    return {"detail": "Task removed from timetable"}

# Additional Features

@app.post("/task/{task_id}/reminder")
def set_task_reminder(task_id: int, reminder_date: date, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    # Here we can add logic for setting a reminder (e.g., sending notification)
    return {"detail": f"Reminder set for task {task.title} on {reminder_date}"}

@app.get("/task/overdue", response_model=List[TaskResponse])
def view_overdue_tasks(db: Session = Depends(get_db)):
    today = date.today()
    tasks = db.query(Task).filter(Task.due_date < today, Task.completed == False).all()
    return tasks

@app.get("/task/weekly-summary", response_model=List[TaskResponse])
def get_weekly_task_summary(db: Session = Depends(get_db)):
    today = date.today()
    week_from_today = today + timedelta(days=7)
    tasks = db.query(Task).filter(Task.due_date.between(today, week_from_today)).all()
    return tasks

@app.get("/task/daily-summary", response_model=List[TaskResponse])
def get_daily_task_summary(db: Session = Depends(get_db)):
    today = date.today()
    tasks = db.query(Task).filter(Task.due_date == today).all()
    return tasks
 