"""Gold tier API endpoints for the AI Employee Dashboard.

Endpoints for Ralph Wiggum tasks, CEO briefings, Meta/Twitter social media,
Odoo invoices, system health, audit logs, and cross-domain search.
"""

import json
import os
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from ai_employee.config import VaultConfig
from ai_employee.services.briefing import BriefingService
from ai_employee.services.meta import MetaService
from ai_employee.services.ralph_wiggum import RalphWiggumService
from ai_employee.services.twitter import TwitterService
from ai_employee.utils.frontmatter import parse_frontmatter

router = APIRouter()


def _get_vault_config() -> VaultConfig:
    """Get vault configuration from environment."""
    vault_path = Path(
        os.environ.get("VAULT_PATH", "~/AI_Employee_Vault")
    ).expanduser()
    return VaultConfig(root=vault_path)


def _extract_context(content: str, query: str) -> str:
    """Extract context around a search match.

    Args:
        content: Full text to search within.
        query: The search term.

    Returns:
        A snippet with surrounding context, or empty string.
    """
    lower_content = content.lower()
    idx = lower_content.find(query.lower())
    if idx == -1:
        return ""
    start = max(0, idx - 50)
    end = min(len(content), idx + len(query) + 50)
    return "..." + content[start:end] + "..."


# ─────────────────────────────────────────────────────────────
# Ralph Wiggum Tasks
# ─────────────────────────────────────────────────────────────


@router.get("/api/tasks")
async def get_tasks() -> dict[str, Any]:
    """Get Ralph Wiggum task states from Active_Tasks."""
    config = _get_vault_config()
    tasks_dir = config.active_tasks

    tasks = []
    if tasks_dir.exists():
        for f in sorted(tasks_dir.glob("*.json"), reverse=True):
            try:
                data = json.loads(f.read_text())
                tasks.append({
                    "id": data.get("task_id", f.stem),
                    "prompt": data.get("prompt", ""),
                    "status": data.get("status", "unknown"),
                    "iteration": data.get("iteration", 0),
                    "max_iterations": data.get("max_iterations", 10),
                    "created_at": data.get("created_at", ""),
                })
            except (json.JSONDecodeError, OSError):
                continue

    return {"count": len(tasks), "tasks": tasks}


@router.post("/api/tasks")
async def create_task(request: Request) -> dict[str, Any]:
    """Create a new Ralph Wiggum autonomous task."""
    data = await request.json()
    config = _get_vault_config()
    service = RalphWiggumService(config)

    prompt = data.get("prompt", "")
    max_iterations = data.get("max_iterations", 10)

    if not prompt:
        raise HTTPException(status_code=400, detail="prompt is required")

    try:
        task = service.start_task(
            prompt=prompt, max_iterations=max_iterations
        )
        return {
            "success": True,
            "task_id": task.task_id,
            "status": task.status.value,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/tasks/{task_id}/pause")
async def pause_task(task_id: str, request: Request) -> dict[str, Any]:
    """Pause a running task for human approval."""
    config = _get_vault_config()
    service = RalphWiggumService(config)

    data = (
        await request.json()
        if request.headers.get("content-type") == "application/json"
        else {}
    )
    approval_id = data.get("approval_id", f"manual_pause_{task_id}")

    try:
        service.pause_task(task_id, approval_id=approval_id)
        return {"success": True, "message": f"Task {task_id} paused"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/tasks/{task_id}/resume")
async def resume_task(task_id: str) -> dict[str, Any]:
    """Resume a paused task."""
    config = _get_vault_config()
    service = RalphWiggumService(config)

    try:
        service.resume_task(task_id)
        return {"success": True, "message": f"Task {task_id} resumed"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─────────────────────────────────────────────────────────────
# CEO Briefings
# ─────────────────────────────────────────────────────────────


@router.get("/api/briefings")
async def get_briefings() -> dict[str, Any]:
    """Get generated CEO briefings."""
    config = _get_vault_config()
    briefings_dir = config.briefings

    briefings = []
    if briefings_dir.exists():
        for f in sorted(briefings_dir.glob("*.md"), reverse=True)[:20]:
            content = f.read_text()
            fm, body = parse_frontmatter(content)
            briefings.append({
                "filename": f.name,
                "generated": fm.get("generated", ""),
                "period": fm.get("period", ""),
                "preview": body[:200] if body else "",
            })

    return {"count": len(briefings), "briefings": briefings}


@router.get("/api/briefings/{filename}")
async def get_briefing_detail(filename: str) -> dict[str, Any]:
    """Get full briefing content by filename."""
    config = _get_vault_config()
    briefings_dir = config.briefings

    if not filename.endswith(".md"):
        raise HTTPException(status_code=404, detail="Briefing not found")

    filepath = briefings_dir / filename
    # Path traversal protection
    if not filepath.resolve().parent == briefings_dir.resolve():
        raise HTTPException(status_code=404, detail="Briefing not found")
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Briefing not found")

    content = filepath.read_text()
    fm, body = parse_frontmatter(content)

    return {
        "filename": filename,
        "generated": fm.get("generated", ""),
        "period": fm.get("period", ""),
        "content": body,
        "frontmatter": fm,
    }


@router.post("/api/briefings/generate")
async def generate_briefing(request: Request) -> dict[str, Any]:
    """Generate a new CEO briefing for a given period."""
    config = _get_vault_config()

    data = (
        await request.json()
        if request.headers.get("content-type") == "application/json"
        else {}
    )

    # Default to last 7 days
    period_end = date.today()
    period_start = period_end - timedelta(days=7)

    if data.get("period_start"):
        period_start = date.fromisoformat(data["period_start"])
    if data.get("period_end"):
        period_end = date.fromisoformat(data["period_end"])

    try:
        service = BriefingService(config)
        briefing = service.generate_briefing(
            period_start=period_start,
            period_end=period_end,
        )
        filepath = service.write_briefing(briefing)

        return {
            "success": True,
            "filename": filepath.name,
            "period": (
                f"{period_start.isoformat()} to {period_end.isoformat()}"
            ),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
# Meta (Facebook/Instagram) Posts
# ─────────────────────────────────────────────────────────────


@router.get("/api/social/meta")
async def get_meta_posts() -> dict[str, Any]:
    """Get Meta (Facebook/Instagram) posts from vault."""
    config = _get_vault_config()
    service = MetaService(config)

    posts = service.list_posts(limit=20)

    post_list = []
    for post in posts:
        post_list.append({
            "id": post.id,
            "platform": post.platform,
            "content": post.content[:200],
            "status": post.status.value,
            "created_at": (
                post.created_at.isoformat() if post.created_at else ""
            ),
            "posted_time": (
                post.posted_time.isoformat()
                if post.posted_time
                else None
            ),
            "platform_id": post.platform_id,
        })

    return {"count": len(post_list), "posts": post_list}


@router.post("/api/social/meta")
async def create_meta_post(request: Request) -> dict[str, Any]:
    """Create a new Meta post (saved locally in vault)."""
    data = await request.json()
    config = _get_vault_config()
    service = MetaService(config)

    content = data.get("content", "")
    platform = data.get("platform", "facebook")

    if not content:
        raise HTTPException(
            status_code=400, detail="content is required"
        )

    post = service.create_post(
        content=content,
        platform=platform,
        media_urls=data.get("media_urls"),
    )

    return {
        "success": True,
        "post_id": post.id,
        "platform": post.platform,
        "status": post.status.value,
    }


@router.post("/api/social/meta/{post_id}/publish")
async def publish_meta_post(post_id: str) -> dict[str, Any]:
    """Publish a Meta post (requires API connection)."""
    config = _get_vault_config()
    service = MetaService(config)

    app_id = os.environ.get("META_APP_ID", "")
    app_secret = os.environ.get("META_APP_SECRET", "")
    access_token = os.environ.get("META_ACCESS_TOKEN", "")
    page_id = os.environ.get("META_PAGE_ID", "")

    if not all([app_id, app_secret, access_token, page_id]):
        raise HTTPException(
            status_code=503,
            detail="Meta API credentials not configured",
        )

    connected = service.connect(
        app_id=app_id,
        app_secret=app_secret,
        access_token=access_token,
        page_id=page_id,
    )

    if not connected:
        raise HTTPException(
            status_code=503,
            detail="Failed to connect to Meta API",
        )

    try:
        published = service.publish_post(post_id)
        return {
            "success": True,
            "post_id": published.id,
            "platform_id": published.platform_id,
            "status": published.status.value,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
# Twitter
# ─────────────────────────────────────────────────────────────


@router.get("/api/social/twitter")
async def get_tweets() -> dict[str, Any]:
    """Get tweets from vault."""
    config = _get_vault_config()
    tweets_dir = config.social_twitter_tweets

    tweet_list = []
    if tweets_dir.exists():
        for f in sorted(tweets_dir.glob("*.md"), reverse=True)[:20]:
            content = f.read_text()
            fm, body = parse_frontmatter(content)
            if fm.get("id"):
                tweet_list.append({
                    "id": fm.get("id", ""),
                    "content": body[:280] if body else "",
                    "status": fm.get("status", "draft"),
                    "twitter_id": fm.get("twitter_id"),
                    "created_at": fm.get("created_at", ""),
                    "posted_time": fm.get("posted_time"),
                    "is_thread": fm.get("is_thread", False),
                })

    return {"count": len(tweet_list), "tweets": tweet_list}


@router.post("/api/social/twitter")
async def create_tweet(request: Request) -> dict[str, Any]:
    """Create a new tweet (saved locally in vault)."""
    data = await request.json()
    config = _get_vault_config()
    service = TwitterService(config)

    content = data.get("content", "")

    if not content:
        raise HTTPException(
            status_code=400, detail="content is required"
        )

    tweet = service.create_tweet(content=content)

    return {
        "success": True,
        "tweet_id": tweet.id,
        "status": tweet.status.value,
    }


@router.post("/api/social/twitter/{tweet_id}/publish")
async def publish_tweet(tweet_id: str) -> dict[str, Any]:
    """Publish a tweet (requires API connection)."""
    config = _get_vault_config()
    service = TwitterService(config)

    api_key = os.environ.get("TWITTER_API_KEY", "")
    api_secret = os.environ.get("TWITTER_API_SECRET", "")
    access_token = os.environ.get("TWITTER_ACCESS_TOKEN", "")
    access_secret = os.environ.get("TWITTER_ACCESS_SECRET", "")
    bearer_token = os.environ.get("TWITTER_BEARER_TOKEN", "")

    if not all([
        api_key, api_secret, access_token, access_secret, bearer_token
    ]):
        raise HTTPException(
            status_code=503,
            detail="Twitter API credentials not configured",
        )

    connected = service.connect(
        api_key=api_key,
        api_secret=api_secret,
        access_token=access_token,
        access_secret=access_secret,
        bearer_token=bearer_token,
    )

    if not connected:
        raise HTTPException(
            status_code=503,
            detail="Failed to connect to Twitter API",
        )

    try:
        published = service.publish_tweet(tweet_id)
        return {
            "success": True,
            "tweet_id": published.id,
            "twitter_id": published.twitter_id,
            "status": published.status.value,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
# Invoices (Odoo)
# ─────────────────────────────────────────────────────────────


@router.get("/api/invoices")
async def get_invoices() -> dict[str, Any]:
    """Get invoices from vault (Odoo integration)."""
    config = _get_vault_config()
    invoices_dir = config.accounting_invoices

    invoice_list = []
    if invoices_dir.exists():
        for f in sorted(invoices_dir.glob("*.md"), reverse=True)[:20]:
            content = f.read_text()
            fm, body = parse_frontmatter(content)
            if fm.get("id"):
                invoice_list.append({
                    "id": fm.get("id", ""),
                    "customer": fm.get("customer_name", ""),
                    "amount": fm.get("amount_total", 0),
                    "status": fm.get("status", "draft"),
                    "date": fm.get("invoice_date", ""),
                    "due_date": fm.get("due_date", ""),
                })

    return {"count": len(invoice_list), "invoices": invoice_list}


@router.post("/api/invoices")
async def create_invoice(request: Request) -> dict[str, Any]:
    """Create a new invoice via Odoo (requires connection)."""
    raise HTTPException(
        status_code=503,
        detail=(
            "Odoo connection required - configure "
            "ODOO_URL, ODOO_DB, ODOO_USER, ODOO_API_KEY"
        ),
    )


# ─────────────────────────────────────────────────────────────
# Health, Audit, Cross-Domain Correlations
# ─────────────────────────────────────────────────────────────


@router.get("/api/health")
async def get_health() -> dict[str, Any]:
    """Get system health status for all services."""
    config = _get_vault_config()

    services = {
        "vault": {
            "status": "healthy",
            "message": "Vault accessible",
        },
        "odoo": {
            "status": (
                "configured"
                if os.environ.get("ODOO_URL")
                else "not_configured"
            ),
            "message": "Odoo ERP integration",
        },
        "meta": {
            "status": (
                "configured"
                if os.environ.get("META_APP_ID")
                else "not_configured"
            ),
            "message": "Facebook/Instagram integration",
        },
        "twitter": {
            "status": (
                "configured"
                if os.environ.get("TWITTER_API_KEY")
                else "not_configured"
            ),
            "message": "Twitter/X integration",
        },
        "gmail": {
            "status": (
                "configured"
                if os.environ.get("GMAIL_CREDENTIALS_PATH")
                else "not_configured"
            ),
            "message": "Gmail integration",
        },
    }

    if not config.root.exists():
        services["vault"] = {
            "status": "error",
            "message": "Vault not found",
        }

    healthy = sum(
        1
        for s in services.values()
        if s["status"] in ("healthy", "configured")
    )
    total = len(services)

    return {
        "overall": (
            "healthy"
            if services["vault"]["status"] == "healthy"
            else "degraded"
        ),
        "services": services,
        "summary": f"{healthy}/{total} services available",
        "dev_mode": (
            os.environ.get("DEV_MODE", "false").lower() == "true"
        ),
    }


@router.get("/api/audit")
async def get_audit_log() -> dict[str, Any]:
    """Get recent audit log entries."""
    config = _get_vault_config()
    logs_dir = config.logs

    entries: list[dict[str, Any]] = []
    if logs_dir.exists():
        # Check both .jsonl and .log files (AuditService uses .log)
        for pattern in ("audit_*.jsonl", "audit_*.log"):
            for f in sorted(
                logs_dir.glob(pattern), reverse=True
            )[:5]:
                for line in f.read_text().strip().split("\n"):
                    if line.strip():
                        try:
                            entries.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue

    # Sort by timestamp descending, limit to 50
    entries.sort(
        key=lambda e: e.get("timestamp", ""), reverse=True
    )
    entries = entries[:50]

    return {"count": len(entries), "entries": entries}


@router.get("/api/correlations/search")
async def search_correlations(q: str = "") -> dict[str, Any]:
    """Search for cross-domain correlations across vault folders."""
    config = _get_vault_config()

    if not q:
        return {"count": 0, "results": [], "query": ""}

    results: list[dict[str, Any]] = []
    search_dirs = [
        config.done,
        config.needs_action,
        config.plans,
        config.briefings,
        config.accounting_invoices,
        config.social_meta_posts,
        config.social_twitter_tweets,
    ]

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        for f in search_dir.glob("*.md"):
            try:
                content = f.read_text()
            except OSError:
                continue
            if q.lower() in content.lower():
                fm, body = parse_frontmatter(content)
                results.append({
                    "file": f.name,
                    "folder": f.parent.name,
                    "id": fm.get("id", f.stem),
                    "preview": body[:150] if body else "",
                    "match_context": _extract_context(content, q),
                })

    return {
        "count": len(results),
        "results": results[:20],
        "query": q,
    }
