# Gold Tier AI Employee - Technology Research

**Created**: 2026-02-21 | **Plan**: [plan.md](./plan.md) | **Spec**: [spec.md](./spec.md)

## Executive Summary

Research on eight key technologies for Gold Tier implementation: Ralph Wiggum loop mechanics, Odoo JSON-RPC integration, Meta Graph API, Twitter/X API v2, CEO Briefing generation patterns, error recovery strategies, watchdog process management, and audit logging best practices.

---

## 1. Ralph Wiggum Autonomous Loop

### Decision
**Implement as a Claude Code Stop hook with file-based state persistence**

### Rationale
- Official pattern documented in Claude Code plugins repository
- Stop hook intercepts exit and can re-inject prompts
- File-based state survives crashes and restarts
- Supports both promise-based and file-movement completion strategies

### Reference Implementation
```text
https://github.com/anthropics/claude-code/tree/main/.claude/plugins/ralph-wiggum
```

### Key Implementation Patterns
```bash
# Stop hook script (.claude/hooks/ralph-wiggum-stop.sh)
#!/bin/bash

STATE_FILE="/path/to/vault/Active_Tasks/current_task.json"

# Check if task file exists and is not in /Done
if [ -f "$STATE_FILE" ]; then
    DONE_CHECK=$(jq -r '.status' "$STATE_FILE")
    if [ "$DONE_CHECK" != "completed" ]; then
        # Block exit and re-inject
        cat "$STATE_FILE" | jq -r '.prompt'
        exit 1  # Non-zero blocks exit
    fi
fi

exit 0  # Allow exit
```

### State File Schema
```json
{
  "task_id": "uuid",
  "prompt": "Original task prompt",
  "iteration": 3,
  "max_iterations": 10,
  "status": "in_progress",
  "context": "Previous output and state",
  "completion_strategy": "promise|file_movement",
  "completion_promise": "TASK_COMPLETE",
  "created_at": "2026-02-21T10:00:00Z"
}
```

### Gotchas
- Must handle Claude Code context limits
- State file corruption recovery needed
- Approval pause requires coordination with approval service
- Max iterations prevents runaway loops

---

## 2. Odoo Community ERP Integration

### Decision
**Use `OdooRPC` library for JSON-RPC 2.0 external API access**

### Rationale
- Official external API for Odoo 19+
- No special access or partnership required
- Supports all CRUD operations on models
- Session caching reduces authentication overhead

### Installation
```bash
uv add odoorpc
```

### Key Implementation Patterns
```python
import odoorpc

# Connection with session caching
odoo = odoorpc.ODOO(
    host='localhost',
    port=8069,
    protocol='jsonrpc+ssl'  # Use 'jsonrpc' for HTTP
)

# Authenticate
odoo.login(
    db='company_db',
    login='admin',
    password=os.environ['ODOO_API_KEY']
)

# Create customer (res.partner)
Partner = odoo.env['res.partner']
partner_id = Partner.create({
    'name': 'Client A',
    'email': 'client_a@example.com',
    'is_company': True
})

# Create invoice (account.move)
Invoice = odoo.env['account.move']
invoice_id = Invoice.create({
    'move_type': 'out_invoice',
    'partner_id': partner_id,
    'invoice_line_ids': [
        (0, 0, {
            'name': 'Consulting Services',
            'quantity': 10,
            'price_unit': 150.00
        })
    ]
})

# Post the invoice
Invoice.browse(invoice_id).action_post()

# Query financials
invoices = Invoice.search_read(
    [('state', '=', 'posted'), ('move_type', '=', 'out_invoice')],
    ['name', 'amount_total', 'amount_residual', 'partner_id']
)
```

### Offline Queue Pattern
```python
from pathlib import Path
import json

QUEUE_FILE = Path("vault/Accounting/pending_operations.jsonl")

def queue_operation(operation: dict):
    """Queue operation when Odoo is unavailable."""
    with open(QUEUE_FILE, 'a') as f:
        f.write(json.dumps(operation) + '\n')

def process_queue():
    """Process queued operations when Odoo is available."""
    if not QUEUE_FILE.exists():
        return

    with open(QUEUE_FILE, 'r') as f:
        operations = [json.loads(line) for line in f]

    for op in operations:
        try:
            execute_operation(op)
        except Exception as e:
            # Re-queue failed operations
            pass

    QUEUE_FILE.unlink()  # Clear processed queue
```

### Gotchas
- API key is actually user password in Odoo (or API key if configured)
- Invoice must be posted before it affects accounting
- Currency handling required for multi-currency setups
- Odoo's ORM-like syntax differs from standard SQL

---

## 3. Meta Graph API (Facebook/Instagram)

### Decision
**Use `facebook-sdk` for Facebook and Instagram Graph API integration**

### Rationale
- Mature, well-maintained library (8,000+ stars)
- Supports both Facebook Pages and Instagram Business accounts
- Instagram posting via linked Facebook Business account
- Built-in rate limiting handling

### Installation
```bash
uv add facebook-sdk
```

### Key Implementation Patterns
```python
import facebook

# Initialize with long-lived Page Access Token
graph = facebook.GraphAPI(access_token=os.environ['META_ACCESS_TOKEN'])

# Post to Facebook Page
page_id = os.environ['META_PAGE_ID']
post = graph.put_object(
    parent_object=page_id,
    connection_name='feed',
    message='Hello from AI Employee!'
)

# Post with image
graph.put_photo(
    image=open('image.jpg', 'rb'),
    message='Check this out!',
    album_path=f'{page_id}/photos'
)

# Get Page insights (engagement)
insights = graph.get_connections(
    id=page_id,
    connection_name='insights',
    metric='page_impressions,page_engaged_users',
    period='day'
)

# Instagram posting (via Facebook Page)
instagram_id = graph.get_connections(
    id=page_id,
    connection_name='instagram_business_account'
)['id']

# Create media container
container = graph.put_object(
    parent_object=instagram_id,
    connection_name='media',
    image_url='https://example.com/image.jpg',
    caption='Hello Instagram!'
)

# Publish container
graph.put_object(
    parent_object=instagram_id,
    connection_name='media_publish',
    creation_id=container['id']
)
```

### Rate Limiting
```python
from datetime import datetime, timedelta

class MetaRateLimiter:
    """Track API calls to respect 200 calls/user/hour limit."""

    def __init__(self, max_calls=200, window_minutes=60):
        self.max_calls = max_calls
        self.window = timedelta(minutes=window_minutes)
        self.calls = []

    def can_call(self) -> bool:
        now = datetime.now()
        self.calls = [t for t in self.calls if now - t < self.window]
        return len(self.calls) < self.max_calls

    def record_call(self):
        self.calls.append(datetime.now())
```

### Gotchas
- Requires Facebook Business account with linked Instagram
- Page Access Tokens expire - use long-lived tokens (60 days)
- Instagram requires image URL (not direct upload)
- Video posts have additional requirements (under 10 minutes)

---

## 4. Twitter/X API v2

### Decision
**Use `tweepy` v4+ for Twitter API v2 integration**

### Rationale
- Most popular Python Twitter library (10,000+ stars)
- Full v2 API support with streaming
- Built-in rate limiting and pagination
- Supports OAuth 2.0 and 1.0a

### Installation
```bash
uv add tweepy
```

### Key Implementation Patterns
```python
import tweepy

# OAuth 2.0 Bearer Token (app-only)
client = tweepy.Client(bearer_token=os.environ['TWITTER_BEARER_TOKEN'])

# OAuth 1.0a User Context (for posting)
client = tweepy.Client(
    consumer_key=os.environ['TWITTER_API_KEY'],
    consumer_secret=os.environ['TWITTER_API_SECRET'],
    access_token=os.environ['TWITTER_ACCESS_TOKEN'],
    access_token_secret=os.environ['TWITTER_ACCESS_SECRET']
)

# Post a tweet
response = client.create_tweet(text='Hello from AI Employee!')
tweet_id = response.data['id']

# Post a thread
first = client.create_tweet(text='Thread 1/3: Introduction')
second = client.create_tweet(
    text='Thread 2/3: Details',
    in_reply_to_tweet_id=first.data['id']
)
third = client.create_tweet(
    text='Thread 3/3: Conclusion',
    in_reply_to_tweet_id=second.data['id']
)

# Upload media (requires v1.1 endpoint)
auth = tweepy.OAuthHandler(
    os.environ['TWITTER_API_KEY'],
    os.environ['TWITTER_API_SECRET']
)
auth.set_access_token(
    os.environ['TWITTER_ACCESS_TOKEN'],
    os.environ['TWITTER_ACCESS_SECRET']
)
api = tweepy.API(auth)
media = api.media_upload('image.jpg')
client.create_tweet(text='With image!', media_ids=[media.media_id])

# Get mentions
mentions = client.get_users_mentions(
    id=user_id,
    tweet_fields=['created_at', 'text', 'author_id']
)

# Search tweets
tweets = client.search_recent_tweets(
    query='from:username OR @username',
    tweet_fields=['created_at', 'public_metrics']
)
```

### Rate Limits (Free Tier)
| Endpoint | Limit |
|----------|-------|
| POST tweets | 50/day, 17/15min |
| GET mentions | 500/month |
| Search | 500/month |

### Gotchas
- Free tier has severe limitations - consider Basic plan ($100/month)
- Media upload requires v1.1 API (separate auth)
- Character limit is 280 (25,000 for Premium)
- DM access requires elevated access

---

## 5. CEO Briefing Generation

### Decision
**Template-based generation with data aggregation from multiple sources**

### Rationale
- Structured format ensures consistency
- Data-driven insights from Odoo, tasks, and activities
- Pattern matching for subscription analysis
- Jinja2 templating for flexibility

### Briefing Template
```markdown
# Monday Morning CEO Briefing

## Executive Summary
{{ executive_summary }}

## Revenue
- **This Week**: ${{ week_revenue }}
- **MTD**: ${{ mtd_revenue }} ({{ mtd_percentage }}% of ${{ monthly_goal }} target)
- **Trend**: {{ trend }}

## Completed Tasks
{% for task in completed_tasks %}
- [x] {{ task.title }}
{% endfor %}

## Bottlenecks
| Task | Expected | Actual | Delay |
|------|----------|--------|-------|
{% for bottleneck in bottlenecks %}
| {{ bottleneck.task }} | {{ bottleneck.expected }} | {{ bottleneck.actual }} | +{{ bottleneck.delay }} |
{% endfor %}

## Proactive Suggestions

### Cost Optimization
{% for suggestion in cost_suggestions %}
- **{{ suggestion.service }}**: {{ suggestion.reason }}. Cost: ${{ suggestion.cost }}/month.
  - [ACTION] {{ suggestion.action }}
{% endfor %}

### Upcoming Deadlines
{% for deadline in deadlines %}
- {{ deadline.task }}: {{ deadline.date }} ({{ deadline.days_remaining }} days)
{% endfor %}

---
*Generated by AI Employee v0.3*
```

### Subscription Analysis Pattern
```python
SUBSCRIPTION_PATTERNS = {
    'netflix.com': 'Netflix',
    'spotify.com': 'Spotify',
    'adobe.com': 'Adobe Creative Cloud',
    'notion.so': 'Notion',
    'slack.com': 'Slack',
    'github.com': 'GitHub',
    'aws.amazon.com': 'AWS',
    'digitalocean.com': 'DigitalOcean'
}

def analyze_subscriptions(transactions: list, activity_logs: dict) -> list:
    """Identify unused subscriptions."""
    suggestions = []

    for tx in transactions:
        for pattern, name in SUBSCRIPTION_PATTERNS.items():
            if pattern in tx['description'].lower():
                # Check if service was used in last 30 days
                last_activity = activity_logs.get(name)
                if not last_activity or (datetime.now() - last_activity).days > 30:
                    suggestions.append({
                        'service': name,
                        'reason': f'No activity in {(datetime.now() - last_activity).days if last_activity else "45+"} days',
                        'cost': tx['amount'],
                        'action': 'Cancel subscription?'
                    })

    return suggestions
```

### Gotchas
- Odoo data may have timezone differences
- Task completion time requires tracking start/end
- Subscription patterns need manual maintenance
- Executive summary requires AI summarization

---

## 6. Error Recovery & Graceful Degradation

### Decision
**Implement retry decorator with exponential backoff and error classification**

### Rationale
- Standard pattern for handling transient failures
- Error classification enables appropriate response
- Component isolation prevents cascading failures
- Queue-based recovery for critical operations

### Retry Decorator
```python
import time
from functools import wraps
from enum import Enum

class ErrorCategory(Enum):
    TRANSIENT = 'transient'      # Network, timeout - retry
    AUTHENTICATION = 'auth'      # Token expired - pause + alert
    LOGIC = 'logic'              # Invalid data - quarantine
    DATA = 'data'                # Corrupted - quarantine + alert
    SYSTEM = 'system'            # Disk full - halt + alert

def classify_error(error: Exception) -> ErrorCategory:
    """Classify error for appropriate handling."""
    if isinstance(error, (ConnectionError, TimeoutError)):
        return ErrorCategory.TRANSIENT
    if 'unauthorized' in str(error).lower() or 'auth' in str(error).lower():
        return ErrorCategory.AUTHENTICATION
    if isinstance(error, (ValueError, TypeError)):
        return ErrorCategory.LOGIC
    if isinstance(error, (IOError, OSError)):
        return ErrorCategory.SYSTEM
    return ErrorCategory.TRANSIENT

def with_retry(max_attempts=3, base_delay=1, max_delay=60):
    """Retry decorator with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    category = classify_error(e)

                    if category == ErrorCategory.TRANSIENT:
                        if attempt == max_attempts - 1:
                            raise
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        time.sleep(delay)
                    elif category == ErrorCategory.AUTHENTICATION:
                        # Don't retry auth errors
                        raise AuthenticationError(str(e))
                    else:
                        raise
            return None
        return wrapper
    return decorator
```

### Graceful Degradation Pattern
```python
class DegradedState:
    """Track component health and degraded functionality."""

    def __init__(self):
        self.healthy_components = set()
        self.degraded_components = {}

    def mark_healthy(self, component: str):
        self.healthy_components.add(component)
        self.degraded_components.pop(component, None)

    def mark_degraded(self, component: str, reason: str):
        self.healthy_components.discard(component)
        self.degraded_components[component] = {
            'reason': reason,
            'since': datetime.now().isoformat()
        }

    def can_operate(self, required_components: list) -> bool:
        """Check if operation can proceed with current health."""
        # Critical components must be healthy
        critical = {'filesystem', 'dashboard'}
        for component in required_components:
            if component in critical and component not in self.healthy_components:
                return False
        return True
```

### Gotchas
- Authentication errors should not be retried
- Some operations (payments) should never auto-retry
- Degraded state must be persisted across restarts
- Alert fatigue - batch similar errors

---

## 7. Watchdog Process Management

### Decision
**Implement Python watchdog with PID monitoring and auto-restart**

### Rationale
- Lightweight, no external dependencies
- PID file tracking for process monitoring
- Configurable restart behavior
- Integration with Dashboard for visibility

### Implementation Pattern
```python
import subprocess
import time
from pathlib import Path
import signal
import os

PROCESSES = {
    'gmail_watcher': {
        'cmd': ['uv', 'run', 'ai-employee', 'watch-gmail', '--vault', '~/AI_Employee_Vault'],
        'critical': True,
        'restart_delay': 5
    },
    'whatsapp_watcher': {
        'cmd': ['uv', 'run', 'ai-employee', 'watch-whatsapp', '--vault', '~/AI_Employee_Vault'],
        'critical': False,
        'restart_delay': 10
    },
    'approval_watcher': {
        'cmd': ['uv', 'run', 'ai-employee', 'watch-approvals', '--vault', '~/AI_Employee_Vault'],
        'critical': True,
        'restart_delay': 5
    }
}

class Watchdog:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.pid_dir = self.vault_path / '.pids'
        self.pid_dir.mkdir(exist_ok=True)
        self.processes = {}

    def get_pid_file(self, name: str) -> Path:
        return self.pid_dir / f'{name}.pid'

    def is_process_running(self, name: str) -> bool:
        pid_file = self.get_pid_file(name)
        if not pid_file.exists():
            return False

        pid = int(pid_file.read_text().strip())
        try:
            os.kill(pid, 0)  # Check if process exists
            return True
        except OSError:
            return False

    def start_process(self, name: str, config: dict):
        proc = subprocess.Popen(
            config['cmd'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        self.get_pid_file(name).write_text(str(proc.pid))
        self.processes[name] = proc
        return proc

    def check_and_restart(self):
        for name, config in PROCESSES.items():
            if not self.is_process_running(name):
                self.log_restart(name)
                time.sleep(config['restart_delay'])
                self.start_process(name, config)
                self.notify_dashboard(name, 'restarted')

    def run(self, check_interval=60):
        while True:
            self.check_and_restart()
            time.sleep(check_interval)
```

### Health Heartbeat Pattern
```python
def heartbeat_check(component: str, vault_path: Path):
    """Write heartbeat to log for uptime tracking."""
    log_file = vault_path / 'Logs' / f'health_{datetime.now().strftime("%Y-%m-%d")}.log'

    with open(log_file, 'a') as f:
        f.write(json.dumps({
            'timestamp': datetime.now().isoformat(),
            'component': component,
            'status': 'alive'
        }) + '\n')
```

### Gotchas
- PID files can become stale after crashes
- Zombie processes need explicit cleanup
- Resource limits (file descriptors) can cause failures
- Signal handling for graceful shutdown

---

## 8. Audit Logging Best Practices

### Decision
**Structured JSON logging with redaction and rotation**

### Rationale
- JSON format enables querying and analysis
- Redaction prevents credential exposure
- Rotation prevents disk exhaustion
- Archive enables historical queries

### Audit Entry Schema
```python
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Any

@dataclass
class AuditEntry:
    timestamp: str
    action_type: str        # email_send, invoice_create, etc.
    actor: str              # claude_code, scheduler, user
    target: str             # recipient, entity ID
    parameters: dict        # Action-specific params
    approval_status: str    # not_required, pending, approved, rejected
    approved_by: Optional[str]
    result: str             # success, failure, partial
    error_message: Optional[str] = None
    correlation_id: Optional[str] = None
    duration_ms: Optional[int] = None

    def to_json(self) -> str:
        return json.dumps(asdict(self))
```

### Redaction Pattern
```python
SENSITIVE_PATTERNS = [
    (r'password["\s:=]+["\']?([^"\'\s]+)', 'password="[REDACTED]"'),
    (r'api_key["\s:=]+["\']?([^"\'\s]+)', 'api_key="[REDACTED]"'),
    (r'token["\s:=]+["\']?([^"\'\s]+)', 'token="[REDACTED]"'),
    (r'secret["\s:=]+["\']?([^"\'\s]+)', 'secret="[REDACTED]"'),
    (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL_REDACTED]'),
    (r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CARD_REDACTED]')
]

def redact_sensitive(text: str) -> str:
    """Redact sensitive data from log entries."""
    import re
    result = text
    for pattern, replacement in SENSITIVE_PATTERNS:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result
```

### Log Rotation and Archival
```python
import gzip
import sqlite3
from pathlib import Path

class AuditArchiver:
    def __init__(self, vault_path: str, retention_days: int = 90):
        self.logs_dir = Path(vault_path) / 'Logs'
        self.archive_dir = Path(vault_path) / 'Archive'
        self.archive_dir.mkdir(exist_ok=True)
        self.retention_days = retention_days
        self.db_path = self.archive_dir / 'audit_archive.db'

    def archive_old_logs(self):
        """Compress and archive logs older than retention period."""
        cutoff = datetime.now() - timedelta(days=self.retention_days)

        for log_file in self.logs_dir.glob('audit_*.jsonl'):
            log_date = datetime.strptime(log_file.stem.split('_')[1], '%Y-%m-%d')
            if log_date < cutoff:
                # Import to SQLite for querying
                self._import_to_sqlite(log_file)

                # Compress original
                with open(log_file, 'rb') as f_in:
                    with gzip.open(f'{log_file}.gz', 'wb') as f_out:
                        f_out.writelines(f_in)

                log_file.unlink()  # Remove original

    def _import_to_sqlite(self, log_file: Path):
        """Import JSONL to SQLite for efficient querying."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_entries (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                action_type TEXT,
                actor TEXT,
                target TEXT,
                result TEXT,
                raw_json TEXT
            )
        ''')

        with open(log_file, 'r') as f:
            for line in f:
                entry = json.loads(line)
                cursor.execute(
                    'INSERT INTO audit_entries VALUES (NULL, ?, ?, ?, ?, ?, ?)',
                    (entry['timestamp'], entry['action_type'], entry['actor'],
                     entry['target'], entry['result'], line)
                )

        conn.commit()
        conn.close()
```

### Gotchas
- SQLite locking with concurrent access
- Disk space monitoring required
- Archive queries are slower - optimize indexes
- Compliance requirements may extend retention

---

## Dependency Summary

```toml
# pyproject.toml additions for Gold Tier
dependencies = [
    # Existing Silver dependencies...
    "odoorpc>=0.9",               # Odoo JSON-RPC
    "facebook-sdk>=3.1",          # Meta Graph API
    "tweepy>=4.14",               # Twitter API v2
    "jinja2>=3.1",                # Briefing templates
]
```

```bash
# Installation
uv add odoorpc facebook-sdk tweepy jinja2
```

---

## Environment Variables (Complete)

```bash
# .env file (gitignored)

# Existing Silver variables...

# Odoo ERP
ODOO_URL=http://localhost:8069
ODOO_DB=company_db
ODOO_USER=admin
ODOO_API_KEY=your_odoo_api_key

# Meta Graph API
META_APP_ID=your_meta_app_id
META_APP_SECRET=your_meta_app_secret
META_ACCESS_TOKEN=your_long_lived_token
META_PAGE_ID=your_page_id

# Twitter/X API v2
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_SECRET=your_access_secret
TWITTER_BEARER_TOKEN=your_bearer_token

# Audit settings
AUDIT_RETENTION_DAYS=90
```

---

## Technology Compatibility Matrix

| Technology | Python Version | Status | Notes |
|------------|---------------|--------|-------|
| odoorpc | 3.7+ | ✅ Compatible | Stable, production-ready |
| facebook-sdk | 3.6+ | ✅ Compatible | Well-maintained |
| tweepy | 3.7+ | ✅ Compatible | Popular, active development |
| jinja2 | 3.7+ | ✅ Compatible | Standard templating |

All technologies are compatible with Python 3.13+ and can coexist using UV package manager.
