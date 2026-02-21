"""AI Employee Dashboard Server.

A Mission Control-style dashboard for monitoring and managing your AI Employee.
Bronze/Silver tier endpoints live here; Gold tier endpoints are in gold_routes.py.
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
from ai_employee.services.processor import ItemProcessor
from ai_employee.models.approval_request import ApprovalCategory

app = FastAPI(title="AI Employee Dashboard", version="1.0.0")

# Setup paths
DASHBOARD_DIR = Path(__file__).parent
STATIC_DIR = DASHBOARD_DIR / "static"
TEMPLATES_DIR = DASHBOARD_DIR / "templates"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Include Gold tier routes
from ai_employee.dashboard.gold_routes import router as gold_router  # noqa: E402

app.include_router(gold_router)


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
    """Approve and execute a pending request."""
    config = get_vault_config()
    approval_service = ApprovalService(config)

    try:
        # First approve the request (moves to Approved folder)
        approved = approval_service.approve_request(approval_id)

        # Then execute the action based on category
        execution_result = {"executed": False, "details": None}

        if approved.category == ApprovalCategory.EMAIL:
            # Execute email send
            email_service = EmailService(config)
            try:
                result = email_service.send_approved_email(approval_id)
                execution_result = {
                    "executed": True,
                    "details": f"Email sent to {', '.join(approved.payload.get('to', []))}"
                }
            except Exception as e:
                execution_result = {"executed": False, "error": str(e)}

        elif approved.category == ApprovalCategory.SOCIAL_POST:
            # Execute LinkedIn post
            linkedin_service = LinkedInService(config)
            try:
                result = linkedin_service.post_approved(approval_id)
                execution_result = {
                    "executed": True,
                    "details": "LinkedIn post published"
                }
            except Exception as e:
                execution_result = {"executed": False, "error": str(e)}

        return {
            "success": True,
            "message": f"Approved: {approval_id}",
            "execution": execution_result
        }
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
            "task_type": task.action.get("type", "custom"),
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


@app.get("/api/plans/{plan_id}")
async def get_plan_detail(plan_id: str) -> dict[str, Any]:
    """Get full plan details with all steps."""
    config = get_vault_config()
    service = PlannerService(config)

    plan = service.get_plan(plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")

    completed = sum(1 for s in plan.steps if s.status.value == "completed")
    steps = []
    for s in plan.steps:
        steps.append({
            "id": s.id,
            "order": s.order,
            "description": s.description,
            "status": s.status.value,
            "requires_approval": s.requires_approval,
            "error": s.error,
            "completed_at": s.completed_at.isoformat() if s.completed_at else None,
        })

    return {
        "id": plan.id,
        "objective": plan.objective,
        "status": plan.status.value,
        "created_at": plan.created_at.isoformat(),
        "completed_at": plan.completed_at.isoformat() if plan.completed_at else None,
        "completion_summary": plan.completion_summary,
        "steps": steps,
        "steps_total": len(plan.steps),
        "steps_completed": completed,
        "progress": int((completed / len(plan.steps)) * 100) if plan.steps else 0,
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


@app.post("/api/inbox/process")
async def process_inbox(request: Request) -> dict[str, Any]:
    """Process pending items in the inbox."""
    config = get_vault_config()
    processor = ItemProcessor(config)

    try:
        # Get pending items
        pending = processor.get_pending_items()
        pending_count = len(pending)

        if pending_count == 0:
            return {
                "success": True,
                "message": "No items to process",
                "processed": 0,
                "success_count": 0,
                "failed_count": 0,
            }

        # Process items (limit to avoid long requests)
        data = await request.json() if request.headers.get("content-type") == "application/json" else {}
        max_items = data.get("max_items", 5)

        success_count = 0
        failed_count = 0
        processed_items = []

        for item_path in pending[:max_items]:
            try:
                result = processor.process_item(item_path)
                if result:
                    success_count += 1
                    processed_items.append({"file": item_path.name, "status": "success"})
                else:
                    failed_count += 1
                    processed_items.append({"file": item_path.name, "status": "failed"})
            except Exception as e:
                failed_count += 1
                processed_items.append({"file": item_path.name, "status": "error", "error": str(e)})

        return {
            "success": True,
            "message": f"Processed {success_count + failed_count} items",
            "processed": success_count + failed_count,
            "success_count": success_count,
            "failed_count": failed_count,
            "remaining": pending_count - (success_count + failed_count),
            "items": processed_items,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/plans/create")
async def create_plan(request: Request) -> dict[str, Any]:
    """Create a new plan."""
    data = await request.json()

    config = get_vault_config()
    service = PlannerService(config)

    try:
        # Extract plan details
        task = data.get("task", "")
        objective = data.get("objective", "")
        steps = data.get("steps", [])

        if not task or not objective:
            raise HTTPException(status_code=400, detail="task and objective are required")

        # Create the plan
        plan = service.create_plan(
            task=task,
            objective=objective,
            steps=[{"description": s, "order": i + 1} for i, s in enumerate(steps)] if steps else None,
        )

        return {
            "success": True,
            "plan_id": plan.id,
            "objective": plan.objective,
            "steps_count": len(plan.steps),
            "status": plan.status.value,
        }
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
