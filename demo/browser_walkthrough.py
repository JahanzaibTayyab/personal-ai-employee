"""
Playwright Browser Walkthrough for AI Employee Demo Video.

Automates a full walkthrough of the web dashboard, clicking through
all 3 tabs, opening modals, filling forms, and demonstrating
cross-domain search. Run this while screen-recording with OBS/QuickTime.

Usage:
    # Start the dashboard first:
    VAULT_PATH=/tmp/demo_vault uv run ai-employee web --port 8000

    # Then run this walkthrough:
    python demo/browser_walkthrough.py

    # Or with screenshots saved:
    python demo/browser_walkthrough.py --screenshots demo/output/

Requirements:
    pip install playwright
    playwright install chromium
"""

import argparse
import sys
import time
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Playwright not installed. Install with:")
    print("  pip install playwright && playwright install chromium")
    sys.exit(1)


PAUSE_SHORT = 1.5
PAUSE_MEDIUM = 2.5
PAUSE_LONG = 4.0
BASE_URL = "http://127.0.0.1:8000"


def take_screenshot(page, screenshots_dir: Path | None, name: str) -> None:
    if screenshots_dir is not None:
        path = screenshots_dir / f"{name}.png"
        page.screenshot(path=str(path), full_page=False)
        print(f"  Screenshot saved: {path}")


def log_step(step: int, description: str) -> None:
    print(f"\n{'='*60}")
    print(f"  Step {step}: {description}")
    print(f"{'='*60}")


def run_walkthrough(screenshots_dir: Path | None = None) -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--start-maximized"],
        )
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            no_viewport=False,
        )
        page = context.new_page()

        # ── Step 1: Navigate to dashboard ────────────────────────
        log_step(1, "Open dashboard")
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        time.sleep(PAUSE_LONG)
        take_screenshot(page, screenshots_dir, "01-overview-loaded")

        # ── Step 2: Scroll through Overview tab ──────────────────
        log_step(2, "Scroll Overview tab — metrics, approvals, plans")
        page.evaluate("window.scrollTo({top: 300, behavior: 'smooth'})")
        time.sleep(PAUSE_MEDIUM)
        take_screenshot(page, screenshots_dir, "02-overview-scrolled")

        page.evaluate("window.scrollTo({top: 600, behavior: 'smooth'})")
        time.sleep(PAUSE_MEDIUM)
        take_screenshot(page, screenshots_dir, "03-overview-bottom")

        page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
        time.sleep(PAUSE_SHORT)

        # ── Step 3: Click an approval item ───────────────────────
        log_step(3, "Click approval item to view details")
        approval_items = page.query_selector_all("#approvals-list .list-item")
        if approval_items:
            approval_items[0].click()
            time.sleep(PAUSE_LONG)
            take_screenshot(page, screenshots_dir, "04-approval-detail")

            close_btn = page.query_selector("#detail-modal .modal-close")
            if close_btn:
                close_btn.click()
            time.sleep(PAUSE_SHORT)
        else:
            print("  (No approval items found)")

        # ── Step 4: Click a plan item ────────────────────────────
        log_step(4, "Click plan to view steps and progress")
        plan_items = page.query_selector_all("#plans-list .list-item")
        if plan_items:
            plan_items[0].click()
            time.sleep(PAUSE_LONG)
            take_screenshot(page, screenshots_dir, "05-plan-detail")

            close_btn = page.query_selector("#detail-modal .modal-close")
            if close_btn:
                close_btn.click()
            time.sleep(PAUSE_SHORT)
        else:
            print("  (No plan items found)")

        # ── Step 5: Open Send Email quick action ─────────────────
        log_step(5, "Open 'Send Email' quick action and fill form")
        email_btn = page.query_selector("button.action-btn:has-text('Send Email')")
        if email_btn:
            email_btn.click()
            time.sleep(PAUSE_MEDIUM)

            page.fill("#email-to", "board@company.com")
            time.sleep(0.5)
            page.fill("#email-cc", "cfo@company.com")
            time.sleep(0.5)
            page.fill("#email-subject", "Q1 2026 Revenue Report")
            time.sleep(0.5)
            page.fill(
                "#email-body",
                "Dear Board,\n\nQ1 revenue reached $64,000 — 18% growth QoQ.\n\nBest regards,\nAI Employee",
            )
            time.sleep(PAUSE_LONG)
            take_screenshot(page, screenshots_dir, "06-email-form")

            cancel_btn = page.query_selector("#email-modal .btn--secondary")
            if cancel_btn:
                cancel_btn.click()
            time.sleep(PAUSE_SHORT)
        else:
            print("  (Send Email button not found)")

        # ── Step 6: Switch to Social Media tab ───────────────────
        log_step(6, "Switch to Social Media tab")
        social_tab = page.query_selector("button.tab-trigger[data-tab='social']")
        if social_tab:
            social_tab.click()
            time.sleep(PAUSE_LONG)
            take_screenshot(page, screenshots_dir, "07-social-tab")

        # ── Step 7: Click a Meta post ────────────────────────────
        log_step(7, "Click Meta post to view details")
        meta_items = page.query_selector_all("#meta-list .list-item")
        if meta_items:
            meta_items[0].click()
            time.sleep(PAUSE_LONG)
            take_screenshot(page, screenshots_dir, "08-meta-detail")

            close_btn = page.query_selector("#detail-modal .modal-close")
            if close_btn:
                close_btn.click()
            time.sleep(PAUSE_SHORT)
        else:
            print("  (No Meta posts found)")

        # ── Step 8: Click a tweet ────────────────────────────────
        log_step(8, "Click tweet to view details")
        tweet_items = page.query_selector_all("#twitter-list .list-item")
        if tweet_items:
            tweet_items[0].click()
            time.sleep(PAUSE_LONG)
            take_screenshot(page, screenshots_dir, "09-tweet-detail")

            close_btn = page.query_selector("#detail-modal .modal-close")
            if close_btn:
                close_btn.click()
            time.sleep(PAUSE_SHORT)
        else:
            print("  (No tweets found)")

        # ── Step 9: Switch to Operations tab ─────────────────────
        log_step(9, "Switch to Operations tab")
        ops_tab = page.query_selector("button.tab-trigger[data-tab='operations']")
        if ops_tab:
            ops_tab.click()
            time.sleep(PAUSE_LONG)
            take_screenshot(page, screenshots_dir, "10-operations-tab")

        # ── Step 10: Click a Ralph Wiggum task ───────────────────
        log_step(10, "Click Ralph Wiggum task to view details")
        task_items = page.query_selector_all("#tasks-list .list-item")
        if task_items:
            task_items[0].click()
            time.sleep(PAUSE_LONG)
            take_screenshot(page, screenshots_dir, "11-ralph-task-detail")

            close_btn = page.query_selector("#detail-modal .modal-close")
            if close_btn:
                close_btn.click()
            time.sleep(PAUSE_SHORT)
        else:
            print("  (No Ralph Wiggum tasks found)")

        # ── Step 11: Click a CEO briefing ────────────────────────
        log_step(11, "Click CEO briefing to view full content")
        briefing_items = page.query_selector_all("#briefings-list .list-item")
        if briefing_items:
            briefing_items[0].click()
            time.sleep(PAUSE_LONG)
            take_screenshot(page, screenshots_dir, "12-briefing-detail")

            # Scroll within modal to show full briefing
            modal_body = page.query_selector("#detail-modal-body")
            if modal_body:
                page.evaluate(
                    "document.querySelector('#detail-modal-body').scrollTop = 300"
                )
                time.sleep(PAUSE_MEDIUM)
                take_screenshot(page, screenshots_dir, "13-briefing-scrolled")

            close_btn = page.query_selector("#detail-modal .modal-close")
            if close_btn:
                close_btn.click()
            time.sleep(PAUSE_SHORT)
        else:
            print("  (No briefings found)")

        # ── Step 12: Click an invoice ────────────────────────────
        log_step(12, "Click invoice to view details")
        invoice_items = page.query_selector_all("#invoices-list .list-item")
        if invoice_items:
            invoice_items[0].click()
            time.sleep(PAUSE_LONG)
            take_screenshot(page, screenshots_dir, "14-invoice-detail")

            close_btn = page.query_selector("#detail-modal .modal-close")
            if close_btn:
                close_btn.click()
            time.sleep(PAUSE_SHORT)
        else:
            print("  (No invoices found)")

        # ── Step 13: Cross-domain search ─────────────────────────
        log_step(13, "Cross-domain search: 'Acme'")
        search_input = page.query_selector("#search-query")
        if search_input:
            search_input.fill("Acme")
            time.sleep(0.5)

            search_btn = page.query_selector(
                "button.btn--primary.btn--sm:has-text('Search')"
            )
            if search_btn:
                search_btn.click()
            time.sleep(PAUSE_LONG)
            take_screenshot(page, screenshots_dir, "15-search-results")
        else:
            print("  (Search input not found)")

        # ── Step 14: Scroll audit log ────────────────────────────
        log_step(14, "Scroll to audit log entries")
        page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
        time.sleep(PAUSE_SHORT)

        audit_list = page.query_selector("#audit-list")
        if audit_list:
            audit_list.scroll_into_view_if_needed()
            time.sleep(PAUSE_LONG)
            take_screenshot(page, screenshots_dir, "16-audit-log")
        else:
            print("  (Audit list not found)")

        # ── Step 15: Return to Overview ──────────────────────────
        log_step(15, "Return to Overview tab — final view")
        overview_tab = page.query_selector("button.tab-trigger[data-tab='overview']")
        if overview_tab:
            overview_tab.click()
            time.sleep(PAUSE_SHORT)

        page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
        time.sleep(PAUSE_LONG)
        take_screenshot(page, screenshots_dir, "17-final-overview")

        print("\n" + "=" * 60)
        print("  Walkthrough complete!")
        print("=" * 60)
        time.sleep(PAUSE_LONG)

        browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Employee Dashboard Walkthrough")
    parser.add_argument(
        "--screenshots",
        type=str,
        default=None,
        help="Directory to save screenshots (e.g., demo/output/)",
    )
    args = parser.parse_args()

    screenshots_path = Path(args.screenshots) if args.screenshots else None
    if screenshots_path is not None:
        screenshots_path.mkdir(parents=True, exist_ok=True)

    run_walkthrough(screenshots_path)
