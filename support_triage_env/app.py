from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .env import SupportInboxEnv
from .models import SupportAction
from .tasks import list_tasks


class ResetRequest(BaseModel):
    task_id: str = "duplicate_refund"


env = SupportInboxEnv()
app = FastAPI(title="Support Inbox Triage OpenEnv", version="0.1.0")


@app.get("/")
def root() -> dict:
    return {"name": "support_inbox_triage", "status": "ok"}


@app.get("/health")
def health() -> dict:
    return {"status": "healthy"}


@app.get("/tasks")
def tasks() -> list[dict]:
    return [task.model_dump() for task in list_tasks()]


@app.post("/reset")
def reset(payload: ResetRequest | None = None) -> dict:
    try:
        observation = env.reset(task_id=(payload.task_id if payload else "duplicate_refund"))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return observation.model_dump()


@app.post("/step")
def step(action: SupportAction) -> dict:
    try:
        observation, reward, done, info = env.step(action)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "observation": observation.model_dump(),
        "reward": reward.model_dump(),
        "done": done,
        "info": info.model_dump(),
    }


@app.get("/state")
@app.post("/state")
def state() -> dict:
    return env.state().model_dump()
