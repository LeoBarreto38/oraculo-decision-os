from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.entities import Goal, Hypothesis, Project, ProjectActivity, Task
from app.scheduler.alerts import run_alert_rules
from app.schemas.api import (
    ActivityCreate,
    GoalCreate,
    GoalOut,
    GoalUpdate,
    HypothesisCreate,
    HypothesisOut,
    HypothesisUpdate,
    ProjectCreate,
    ProjectOut,
    ProjectUpdate,
    TaskCreate,
    TaskOut,
    TaskUpdate,
)


router = APIRouter(tags=["resources"])


def _get_or_404(db: Session, model: type, item_id: int):
    item = db.get(model, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Registro não encontrado.")
    return item


def _commit(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Conflito com um registro existente.") from exc


@router.get("/goals", response_model=list[GoalOut])
def list_goals(db: Session = Depends(get_db)):
    return list(db.scalars(select(Goal).order_by(Goal.priority.desc(), Goal.id)))


@router.post("/goals", response_model=GoalOut, status_code=status.HTTP_201_CREATED)
def create_goal(payload: GoalCreate, db: Session = Depends(get_db)):
    item = Goal(**payload.model_dump())
    db.add(item)
    _commit(db)
    db.refresh(item)
    return item


@router.get("/goals/{goal_id}", response_model=GoalOut)
def get_goal(goal_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, Goal, goal_id)


@router.patch("/goals/{goal_id}", response_model=GoalOut)
def update_goal(goal_id: int, payload: GoalUpdate, db: Session = Depends(get_db)):
    item = _get_or_404(db, Goal, goal_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    _commit(db)
    return item


@router.delete("/goals/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(goal_id: int, db: Session = Depends(get_db)):
    db.delete(_get_or_404(db, Goal, goal_id))
    _commit(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/projects", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    return list(db.scalars(select(Project).order_by(Project.strategic_value.desc(), Project.name)))


@router.post("/projects", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    item = Project(**payload.model_dump())
    db.add(item)
    _commit(db)
    db.refresh(item)
    run_alert_rules(db)
    return item


@router.get("/projects/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, Project, project_id)


@router.patch("/projects/{project_id}", response_model=ProjectOut)
def update_project(project_id: int, payload: ProjectUpdate, db: Session = Depends(get_db)):
    item = _get_or_404(db, Project, project_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    _commit(db)
    return item


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    db.delete(_get_or_404(db, Project, project_id))
    _commit(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/projects/{project_id}/activities", status_code=status.HTTP_201_CREATED)
def create_project_activity(project_id: int, payload: ActivityCreate, db: Session = Depends(get_db)):
    project = _get_or_404(db, Project, project_id)
    item = ProjectActivity(
        project_id=project.id,
        **payload.model_dump(exclude={"occurred_at"}),
        occurred_at=payload.occurred_at or datetime.now(timezone.utc),
    )
    project.last_progress_at = item.occurred_at
    db.add(item)
    _commit(db)
    return {
        "id": item.id,
        "project_id": item.project_id,
        "type": item.type,
        "description": item.description,
        "occurred_at": item.occurred_at,
        "is_external": item.is_external,
    }


@router.get("/tasks", response_model=list[TaskOut])
def list_tasks(project_id: int | None = None, status_filter: str | None = None, db: Session = Depends(get_db)):
    query = select(Task)
    if project_id is not None:
        query = query.where(Task.project_id == project_id)
    if status_filter:
        query = query.where(Task.status == status_filter)
    return list(db.scalars(query.order_by(Task.priority.desc(), Task.due_at.asc().nulls_last(), Task.id)))


def _validate_task_links(db: Session, payload: TaskCreate | TaskUpdate) -> None:
    values = payload.model_dump(exclude_unset=True)
    if values.get("project_id") is not None and db.get(Project, values["project_id"]) is None:
        raise HTTPException(status_code=422, detail="project_id não existe.")
    if values.get("goal_id") is not None and db.get(Goal, values["goal_id"]) is None:
        raise HTTPException(status_code=422, detail="goal_id não existe.")


@router.post("/tasks", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    _validate_task_links(db, payload)
    item = Task(**payload.model_dump())
    if item.status in ("DONE", "COMPLETED"):
        item.completed_at = datetime.now(timezone.utc)
    db.add(item)
    _commit(db)
    db.refresh(item)
    return item


@router.get("/tasks/{task_id}", response_model=TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, Task, task_id)


@router.patch("/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db)):
    _validate_task_links(db, payload)
    item = _get_or_404(db, Task, task_id)
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(item, key, value)
    if updates.get("status") in ("DONE", "COMPLETED") and item.completed_at is None:
        item.completed_at = datetime.now(timezone.utc)
        if item.project_id:
            project = db.get(Project, item.project_id)
            if project:
                project.last_progress_at = item.completed_at
                db.add(
                    ProjectActivity(
                        project_id=project.id,
                        type="EXTERNAL" if item.is_external_interaction else "TASK_COMPLETED",
                        description=f"Tarefa concluída: {item.title}",
                        occurred_at=item.completed_at,
                        is_external=item.is_external_interaction,
                    )
                )
    _commit(db)
    return item


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    db.delete(_get_or_404(db, Task, task_id))
    _commit(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/hypotheses", response_model=list[HypothesisOut])
def list_hypotheses(db: Session = Depends(get_db)):
    return list(db.scalars(select(Hypothesis).order_by(Hypothesis.test_due_at.asc().nulls_last(), Hypothesis.id)))


@router.post("/hypotheses", response_model=HypothesisOut, status_code=status.HTTP_201_CREATED)
def create_hypothesis(payload: HypothesisCreate, db: Session = Depends(get_db)):
    if payload.project_id is not None and db.get(Project, payload.project_id) is None:
        raise HTTPException(status_code=422, detail="project_id não existe.")
    item = Hypothesis(**payload.model_dump())
    db.add(item)
    _commit(db)
    db.refresh(item)
    return item


@router.get("/hypotheses/{hypothesis_id}", response_model=HypothesisOut)
def get_hypothesis(hypothesis_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, Hypothesis, hypothesis_id)


@router.patch("/hypotheses/{hypothesis_id}", response_model=HypothesisOut)
def update_hypothesis(hypothesis_id: int, payload: HypothesisUpdate, db: Session = Depends(get_db)):
    item = _get_or_404(db, Hypothesis, hypothesis_id)
    updates = payload.model_dump(exclude_unset=True)
    if updates.get("project_id") is not None and db.get(Project, updates["project_id"]) is None:
        raise HTTPException(status_code=422, detail="project_id não existe.")
    for key, value in updates.items():
        setattr(item, key, value)
    if updates.get("status") in ("VALIDATED", "INVALIDATED", "RESOLVED") and item.resolved_at is None:
        item.resolved_at = datetime.now(timezone.utc)
    _commit(db)
    return item


@router.delete("/hypotheses/{hypothesis_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_hypothesis(hypothesis_id: int, db: Session = Depends(get_db)):
    db.delete(_get_or_404(db, Hypothesis, hypothesis_id))
    _commit(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
