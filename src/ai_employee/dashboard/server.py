"""AI Employee Dashboard Server.

A Mission Control-style dashboard for monitoring and managing your AI Employee.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()

try:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.templating import Jinja2Templates
    import uvicorn
except ImportError:
    print("Dashboard dependencies not installed.")
    print("Run: uv add fastapi uvicorn jinja2 python-multipart")
    raise

from ai_employee.config import VaultConfig
from ai_employee.services.approval import ApprovalService
from ai_employee.services.scheduler import SchedulerService
from ai_employee.services.planner import PlannerService
from ai_employee.services.email import EmailService, EmailDraft
from ai_employee.services.linkedin import LinkedInService
from ai_employee.models.approval_request import ApprovalCategory

app = FastAPI(title="AI Employee Dashboard", version="1.0.0")

# Setup paths
DASHBOARD_DIR = Path(__file__).parent
STATIC_DIR = DASHBOARD_DIR / "static"
TEMPLATES_DIR = DASHBOARD_DIR / "templates"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def get_vault_config() -> VaultConfig:
    """Get vault configuration from environment."""
    vault_path = Path(os.environ.get("VAULT_PATH", "~/AI_Employee_Vault")).expanduser()
    return VaultConfig(root=vault_path)


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Render the main dashboard."""
    return templates.TemplateResponse(request, "dashboard.html")


@app.get("/api/status")
async def get_status() -> dict[str, Any]:
    """Get overall system status."""
    config = get_vault_config()

    # Count items in various folders
    inbox_count = len(list(config.inbox.glob("*"))) if config.inbox.exists() else 0
    needs_action_count = len(list(config.needs_action.rglob("*.md"))) if config.needs_action.exists() else 0
    done_count = len(list(config.done.glob("*.md"))) if config.done.exists() else 0
    quarantine_count = len(list(config.quarantine.glob("*"))) if config.quarantine.exists() else 0

    return {
        "timestamp": datetime.now().isoformat(),
        "vault_path": str(config.root),
        "counts": {
            "inbox": inbox_count,
            "needs_action": needs_action_count,
            "done": done_count,
            "quarantine": quarantine_count,
        },
        "watchers": {
            "file": "stopped",
            "gmail": "stopped",
            "whatsapp": "stopped",
            "approval": "stopped",
        }
    }


@app.get("/api/approvals")
async def get_approvals() -> dict[str, Any]:
    """Get pending approval requests."""
    config = get_vault_config()
    service = ApprovalService(config)

    pending = service.get_pending_requests()

    approvals = []
    for req in pending:
        approvals.append({
            "id": req.id,
            "category": req.category.value,
            "status": req.status.value,
            "summary": req.summary[:100] if req.summary else "",
            "created_at": req.created_at.isoformat(),
            "expires_at": req.expires_at.isoformat() if req.expires_at else None,
            "is_expired": req.is_expired(),
            "payload": req.payload,
        })

    return {
        "count": len(approvals),
        "approvals": approvals,
    }


@app.post("/api/approvals/{approval_id}/approve")
async def approve_request(approval_id: str) -> dict[str, Any]:
    """Approve a pending request."""
    config = get_vault_config()
    service = ApprovalService(config)

    try:
        result = service.approve_request(approval_id)
        return {"success": True, "message": f"Approved: {approval_id}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/approvals/{approval_id}/reject")
async def reject_request(approval_id: str) -> dict[str, Any]:
    """Reject a pending request."""
    config = get_vault_config()
    service = ApprovalService(config)

    try:
        result = service.reject_request(approval_id)
        return {"success": True, "message": f"Rejected: {approval_id}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/schedules")
async def get_schedules() -> dict[str, Any]:
    """Get scheduled tasks."""
    config = get_vault_config()
    service = SchedulerService(config)

    tasks = service.get_all_tasks()

    schedules = []
    for task in tasks:
        schedules.append({
            "id": task.id,
            "name": task.name,
            "schedule": task.schedule,
            "enabled": task.enabled,
            "task_type": task.task_type.value,
            "last_run": task.last_run.isoformat() if task.last_run else None,
            "next_run": task.next_run.isoformat() if task.next_run else None,
        })

    return {
        "count": len(schedules),
        "schedules": schedules,
    }


@app.get("/api/plans")
async def get_plans() -> dict[str, Any]:
    """Get active plans."""
    config = get_vault_config()
    service = PlannerService(config)

    plans = service.get_active_plans()

    plan_list = []
    for plan in plans:
        completed = sum(1 for s in plan.steps if s.status.value == "completed")
        plan_list.append({
            "id": plan.id,
            "task": plan.objective,
            "status": plan.status.value,
            "steps_total": len(plan.steps),
            "steps_completed": completed,
            "progress": int((completed / len(plan.steps)) * 100) if plan.steps else 0,
            "created_at": plan.created_at.isoformat(),
        })

    return {
        "count": len(plan_list),
        "plans": plan_list,
    }


@app.post("/api/email/send")
async def send_email(request: Request) -> dict[str, Any]:
    """Create email approval request."""
    data = await request.json()

    config = get_vault_config()
    service = EmailService(config)

    draft = EmailDraft(
        to=data.get("to", []),
        subject=data.get("subject", ""),
        body=data.get("body", ""),
        cc=data.get("cc", []),
        bcc=data.get("bcc", []),
    )

    try:
        approval_id = service.draft_email(draft)
        return {"success": True, "approval_id": approval_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/linkedin/post")
async def create_linkedin_post(request: Request) -> dict[str, Any]:
    """Create LinkedIn post approval request."""
    data = await request.json()

    config = get_vault_config()
    service = LinkedInService(config)

    try:
        approval_id = service.schedule_post(
            content=data.get("content", ""),
            scheduled_time=datetime.now(),
        )
        return {"success": True, "approval_id": approval_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def run_server(host: str = "127.0.0.1", port: int = 8000):
    """Run the dashboard server."""
    print(f"\n🚀 AI Employee Dashboard starting...")
    print(f"   Open: http://{host}:{port}")
    print(f"   Press Ctrl+C to stop\n")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
