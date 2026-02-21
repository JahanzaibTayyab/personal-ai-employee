/**
 * AI Employee Dashboard - Mission Control
 * Frontend JavaScript for real-time dashboard updates
 */

// Update timestamp
function updateTimestamp() {
    const now = new Date();
    const timestamp = now.toISOString().replace('T', ' ').substring(0, 19);
    document.getElementById('timestamp').textContent = timestamp + ' UTC';
}

// Show toast notification
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast show ${type}`;

    setTimeout(() => {
        toast.className = 'toast';
    }, 3000);
}

// Modal functions
function openModal(modalId) {
    document.getElementById(modalId).classList.add('active');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

function openEmailModal() {
    openModal('email-modal');
}

function openLinkedInModal() {
    openModal('linkedin-modal');
    updateCharCount();
}

function openPlanModal() {
    openModal('plan-modal');
}

// Character count for LinkedIn
function updateCharCount() {
    const content = document.getElementById('linkedin-content');
    const counter = document.getElementById('linkedin-chars');

    if (content && counter) {
        counter.textContent = content.value.length;
    }
}

document.getElementById('linkedin-content')?.addEventListener('input', updateCharCount);

// Close modal on outside click
document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.remove('active');
        }
    });
});

// Close modal on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal.active').forEach(modal => {
            modal.classList.remove('active');
        });
    }
});

// API Functions
async function fetchStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();

        // Update counts
        document.getElementById('inbox-count').textContent = data.counts.inbox;
        document.getElementById('needs-action-count').textContent = data.counts.needs_action;
        document.getElementById('done-count').textContent = data.counts.done;
        document.getElementById('quarantine-count').textContent = data.counts.quarantine;

        // Update watcher statuses
        updateWatcherStatus('file-watcher', data.watchers.file);
        updateWatcherStatus('gmail-watcher', data.watchers.gmail);
        updateWatcherStatus('whatsapp-watcher', data.watchers.whatsapp);
        updateWatcherStatus('approval-watcher', data.watchers.approval);

    } catch (error) {
        console.error('Error fetching status:', error);
    }
}

function updateWatcherStatus(elementId, status) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = status.toUpperCase();
        element.className = 'watcher-indicator' + (status === 'running' ? ' running' : '');
    }
}

async function fetchApprovals() {
    try {
        const response = await fetch('/api/approvals');
        const data = await response.json();

        document.getElementById('approval-badge').textContent = data.count;

        const container = document.getElementById('approvals-list');

        if (data.count === 0) {
            container.innerHTML = '<div class="empty-state">No pending approvals</div>';
            return;
        }

        container.innerHTML = data.approvals.map(approval => `
            <div class="approval-item ${approval.is_expired ? 'expired' : ''}">
                <div class="approval-info">
                    <span class="approval-category ${approval.category}">${approval.category.toUpperCase()}</span>
                    <div class="approval-summary">${escapeHtml(approval.summary || getApprovalSummary(approval))}</div>
                    <div class="approval-meta">
                        ID: ${approval.id.substring(0, 20)}... |
                        Created: ${formatDate(approval.created_at)}
                        ${approval.is_expired ? ' | <span style="color: var(--accent-danger)">EXPIRED</span>' : ''}
                    </div>
                </div>
                <div class="approval-actions">
                    <button class="btn-approve" onclick="approveRequest('${approval.id}')" ${approval.is_expired ? 'disabled' : ''}>
                        APPROVE
                    </button>
                    <button class="btn-reject" onclick="rejectRequest('${approval.id}')" ${approval.is_expired ? 'disabled' : ''}>
                        REJECT
                    </button>
                </div>
            </div>
        `).join('');

    } catch (error) {
        console.error('Error fetching approvals:', error);
        document.getElementById('approvals-list').innerHTML = '<div class="empty-state">Error loading approvals</div>';
    }
}

function getApprovalSummary(approval) {
    if (approval.payload) {
        if (approval.category === 'email') {
            return `Email to ${approval.payload.to?.join(', ') || 'N/A'}: ${approval.payload.subject || 'No subject'}`;
        }
        if (approval.category === 'linkedin') {
            const content = approval.payload.content || '';
            return content.substring(0, 100) + (content.length > 100 ? '...' : '');
        }
    }
    return 'Pending approval';
}

async function fetchSchedules() {
    try {
        const response = await fetch('/api/schedules');
        const data = await response.json();

        document.getElementById('schedule-badge').textContent = data.count;

        const container = document.getElementById('schedules-list');

        if (data.count === 0) {
            container.innerHTML = '<div class="empty-state">No scheduled tasks</div>';
            return;
        }

        container.innerHTML = data.schedules.map(schedule => `
            <div class="schedule-item ${schedule.enabled ? '' : 'disabled'}">
                <div class="schedule-info">
                    <div class="schedule-name">${escapeHtml(schedule.name)}</div>
                    <div class="schedule-cron">${escapeHtml(schedule.schedule)}</div>
                </div>
                <span class="schedule-status ${schedule.enabled ? 'enabled' : 'disabled'}">
                    ${schedule.enabled ? 'ENABLED' : 'DISABLED'}
                </span>
            </div>
        `).join('');

    } catch (error) {
        console.error('Error fetching schedules:', error);
        document.getElementById('schedules-list').innerHTML = '<div class="empty-state">Error loading schedules</div>';
    }
}

async function fetchPlans() {
    try {
        const response = await fetch('/api/plans');
        const data = await response.json();

        document.getElementById('plan-badge').textContent = data.count;

        const container = document.getElementById('plans-list');

        if (data.count === 0) {
            container.innerHTML = '<div class="empty-state">No active plans</div>';
            return;
        }

        container.innerHTML = data.plans.map(plan => `
            <div class="plan-item">
                <div class="plan-header">
                    <div class="plan-objective">${escapeHtml(plan.task)}</div>
                    <span class="plan-status ${plan.status}">${plan.status.toUpperCase()}</span>
                </div>
                <div class="plan-progress">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${plan.progress}%"></div>
                    </div>
                </div>
                <div class="plan-meta">
                    <span>${plan.steps_completed}/${plan.steps_total} steps</span>
                    <span>${plan.progress}% complete</span>
                </div>
            </div>
        `).join('');

    } catch (error) {
        console.error('Error fetching plans:', error);
        document.getElementById('plans-list').innerHTML = '<div class="empty-state">Error loading plans</div>';
    }
}

// Action handlers
async function approveRequest(approvalId) {
    try {
        const response = await fetch(`/api/approvals/${approvalId}/approve`, {
            method: 'POST'
        });

        if (response.ok) {
            showToast('Approval granted', 'success');
            fetchApprovals();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Failed to approve', 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

async function rejectRequest(approvalId) {
    try {
        const response = await fetch(`/api/approvals/${approvalId}/reject`, {
            method: 'POST'
        });

        if (response.ok) {
            showToast('Request rejected', 'success');
            fetchApprovals();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Failed to reject', 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

async function sendEmail(event) {
    event.preventDefault();

    const to = document.getElementById('email-to').value;
    const cc = document.getElementById('email-cc').value;
    const subject = document.getElementById('email-subject').value;
    const body = document.getElementById('email-body').value;

    try {
        const response = await fetch('/api/email/send', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                to: [to],
                cc: cc ? [cc] : [],
                subject,
                body
            })
        });

        if (response.ok) {
            showToast('Email queued for approval', 'success');
            closeModal('email-modal');
            document.getElementById('email-form').reset();
            fetchApprovals();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Failed to send email', 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

async function postLinkedIn(event) {
    event.preventDefault();

    const content = document.getElementById('linkedin-content').value;

    try {
        const response = await fetch('/api/linkedin/post', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ content })
        });

        if (response.ok) {
            showToast('LinkedIn post queued for approval', 'success');
            closeModal('linkedin-modal');
            document.getElementById('linkedin-form').reset();
            updateCharCount();
            fetchApprovals();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Failed to create post', 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

async function createPlan(event) {
    event.preventDefault();

    const task = document.getElementById('plan-objective').value;
    const description = document.getElementById('plan-description').value;

    // Parse description into steps if it contains numbered items
    let steps = [];
    if (description) {
        const lines = description.split('\n').filter(l => l.trim());
        steps = lines.map(l => l.replace(/^\d+[\.\)]\s*/, '').trim()).filter(s => s);
    }

    try {
        const response = await fetch('/api/plans/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                task: task,
                objective: task,
                steps: steps.length > 0 ? steps : [task]
            })
        });

        if (response.ok) {
            const data = await response.json();
            showToast(`Plan created: ${data.plan_id} (${data.steps_count} steps)`, 'success');
            closeModal('plan-modal');
            document.getElementById('plan-form').reset();
            fetchPlans();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Failed to create plan', 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

async function runProcessInbox() {
    showToast('Processing inbox...', 'info');

    try {
        const response = await fetch('/api/inbox/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ max_items: 5 })
        });

        if (response.ok) {
            const data = await response.json();
            if (data.processed === 0) {
                showToast('No items to process', 'info');
            } else {
                showToast(`Processed ${data.success_count} items (${data.failed_count} failed, ${data.remaining} remaining)`, 'success');
            }
            // Refresh status to update counts
            fetchStatus();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Failed to process inbox', 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

// =========================================
// GOLD TIER - Modal openers
// =========================================

function openTaskModal() {
    openModal('task-modal');
}

function openMetaModal() {
    openModal('meta-modal');
}

function openTweetModal() {
    openModal('tweet-modal');
    updateTweetCharCount();
}

function updateTweetCharCount() {
    const content = document.getElementById('tweet-content');
    const counter = document.getElementById('tweet-chars');
    if (content && counter) {
        counter.textContent = content.value.length;
    }
}

document.getElementById('tweet-content')?.addEventListener('input', updateTweetCharCount);

// =========================================
// GOLD TIER - Fetch functions
// =========================================

async function fetchTasks() {
    try {
        const response = await fetch('/api/tasks');
        const data = await response.json();

        const badge = document.getElementById('task-badge');
        if (badge) badge.textContent = data.count;

        const container = document.getElementById('tasks-list');
        if (!container) return;

        if (data.count === 0) {
            container.innerHTML = '<div class="empty-state">No active tasks</div>';
            return;
        }

        container.innerHTML = data.tasks.map(task => `
            <div class="task-item">
                <div class="task-info">
                    <div class="task-prompt">${escapeHtml((task.prompt || '').substring(0, 80))}${(task.prompt || '').length > 80 ? '...' : ''}</div>
                    <div class="task-meta">
                        Status: <span class="task-status ${task.status}">${(task.status || 'unknown').toUpperCase()}</span>
                        | Iteration: ${task.iteration}/${task.max_iterations}
                    </div>
                </div>
                <div class="task-actions">
                    ${task.status === 'running' ? `<button class="btn-small btn-warning" onclick="pauseTask('${task.id}')">PAUSE</button>` : ''}
                    ${task.status === 'paused' ? `<button class="btn-small btn-approve" onclick="resumeTask('${task.id}')">RESUME</button>` : ''}
                </div>
            </div>
        `).join('');
    } catch (error) {
        const container = document.getElementById('tasks-list');
        if (container) container.innerHTML = '<div class="empty-state">Error loading tasks</div>';
    }
}

async function fetchBriefings() {
    try {
        const response = await fetch('/api/briefings');
        const data = await response.json();

        const badge = document.getElementById('briefing-badge');
        if (badge) badge.textContent = data.count;

        const container = document.getElementById('briefings-list');
        if (!container) return;

        if (data.count === 0) {
            container.innerHTML = '<div class="empty-state">No briefings generated yet</div>';
            return;
        }

        container.innerHTML = data.briefings.map(b => `
            <div class="briefing-item">
                <div class="briefing-filename">${escapeHtml(b.filename)}</div>
                <div class="briefing-meta">
                    ${b.period ? `Period: ${escapeHtml(b.period)}` : ''}
                    ${b.generated ? ` | Generated: ${formatDate(b.generated)}` : ''}
                </div>
                <div class="briefing-preview">${escapeHtml(b.preview)}</div>
            </div>
        `).join('');
    } catch (error) {
        const container = document.getElementById('briefings-list');
        if (container) container.innerHTML = '<div class="empty-state">Error loading briefings</div>';
    }
}

async function fetchMetaPosts() {
    try {
        const response = await fetch('/api/social/meta');
        const data = await response.json();

        const badge = document.getElementById('meta-badge');
        if (badge) badge.textContent = data.count;

        const container = document.getElementById('meta-list');
        if (!container) return;

        if (data.count === 0) {
            container.innerHTML = '<div class="empty-state">No Meta posts yet</div>';
            return;
        }

        container.innerHTML = data.posts.map(post => `
            <div class="social-item">
                <div class="social-info">
                    <span class="social-platform ${post.platform}">${(post.platform || '').toUpperCase()}</span>
                    <div class="social-content">${escapeHtml((post.content || '').substring(0, 120))}${(post.content || '').length > 120 ? '...' : ''}</div>
                    <div class="social-meta">
                        Status: <span class="post-status ${post.status}">${(post.status || 'draft').toUpperCase()}</span>
                        ${post.posted_time ? ` | Posted: ${formatDate(post.posted_time)}` : ''}
                    </div>
                </div>
                ${post.status === 'draft' ? `<button class="btn-small btn-approve" onclick="publishMetaPost('${post.id}')">PUBLISH</button>` : ''}
            </div>
        `).join('');
    } catch (error) {
        const container = document.getElementById('meta-list');
        if (container) container.innerHTML = '<div class="empty-state">Error loading Meta posts</div>';
    }
}

async function fetchTweets() {
    try {
        const response = await fetch('/api/social/twitter');
        const data = await response.json();

        const badge = document.getElementById('twitter-badge');
        if (badge) badge.textContent = data.count;

        const container = document.getElementById('twitter-list');
        if (!container) return;

        if (data.count === 0) {
            container.innerHTML = '<div class="empty-state">No tweets yet</div>';
            return;
        }

        container.innerHTML = data.tweets.map(tweet => `
            <div class="social-item">
                <div class="social-info">
                    <div class="social-content">${escapeHtml((tweet.content || '').substring(0, 280))}</div>
                    <div class="social-meta">
                        Status: <span class="post-status ${tweet.status}">${(tweet.status || 'draft').toUpperCase()}</span>
                        ${tweet.is_thread ? ' | Thread' : ''}
                        ${tweet.posted_time ? ` | Posted: ${formatDate(tweet.posted_time)}` : ''}
                    </div>
                </div>
                ${tweet.status === 'draft' ? `<button class="btn-small btn-approve" onclick="publishTweet('${tweet.id}')">PUBLISH</button>` : ''}
            </div>
        `).join('');
    } catch (error) {
        const container = document.getElementById('twitter-list');
        if (container) container.innerHTML = '<div class="empty-state">Error loading tweets</div>';
    }
}

async function fetchInvoices() {
    try {
        const response = await fetch('/api/invoices');
        const data = await response.json();

        const badge = document.getElementById('invoice-badge');
        if (badge) badge.textContent = data.count;

        const container = document.getElementById('invoices-list');
        if (!container) return;

        if (data.count === 0) {
            container.innerHTML = '<div class="empty-state">No invoices</div>';
            return;
        }

        container.innerHTML = data.invoices.map(inv => `
            <div class="invoice-item">
                <div class="invoice-info">
                    <div class="invoice-customer">${escapeHtml(inv.customer || 'Unknown')}</div>
                    <div class="invoice-meta">
                        Amount: $${inv.amount || 0} | Status: ${(inv.status || 'draft').toUpperCase()}
                        ${inv.due_date ? ` | Due: ${inv.due_date}` : ''}
                    </div>
                </div>
            </div>
        `).join('');
    } catch (error) {
        const container = document.getElementById('invoices-list');
        if (container) {
            if (error.message && error.message.includes('503')) {
                container.innerHTML = '<div class="empty-state">Odoo not connected</div>';
            } else {
                container.innerHTML = '<div class="empty-state">No invoices</div>';
            }
        }
    }
}

async function fetchHealth() {
    try {
        const response = await fetch('/api/health');
        const data = await response.json();

        const container = document.getElementById('health-status');
        if (!container) return;

        const services = data.services || {};
        container.innerHTML = `
            <div class="health-overall ${data.overall}">
                SYSTEM: ${(data.overall || 'unknown').toUpperCase()}
                ${data.dev_mode ? ' <span class="dev-mode-badge">DEV MODE</span>' : ''}
            </div>
            <div class="health-services">
                ${Object.entries(services).map(([name, info]) => `
                    <div class="health-service">
                        <span class="service-name">${name.toUpperCase()}</span>
                        <span class="service-status ${info.status}">${(info.status || 'unknown').toUpperCase()}</span>
                    </div>
                `).join('')}
            </div>
            <div class="health-summary">${escapeHtml(data.summary || '')}</div>
        `;
    } catch (error) {
        const container = document.getElementById('health-status');
        if (container) container.innerHTML = '<div class="empty-state">Error checking health</div>';
    }
}

async function fetchAuditLog() {
    try {
        const response = await fetch('/api/audit');
        const data = await response.json();

        const badge = document.getElementById('audit-badge');
        if (badge) badge.textContent = data.count;

        const container = document.getElementById('audit-list');
        if (!container) return;

        if (data.count === 0) {
            container.innerHTML = '<div class="empty-state">No audit entries</div>';
            return;
        }

        container.innerHTML = data.entries.slice(0, 10).map(entry => `
            <div class="audit-item">
                <span class="audit-time">${(entry.timestamp || '').substring(11, 19)}</span>
                <span class="audit-action">${escapeHtml(entry.action_type || entry.operation || 'action')}</span>
                <span class="audit-result ${entry.result || (entry.success ? 'success' : 'failure')}">${entry.result || (entry.success ? 'OK' : 'FAIL')}</span>
            </div>
        `).join('');
    } catch (error) {
        const container = document.getElementById('audit-list');
        if (container) container.innerHTML = '<div class="empty-state">No audit entries</div>';
    }
}

// =========================================
// GOLD TIER - Action handlers
// =========================================

async function createTask(event) {
    event.preventDefault();
    const prompt = document.getElementById('task-prompt').value;
    const maxIter = parseInt(document.getElementById('task-max-iter').value) || 10;

    try {
        const response = await fetch('/api/tasks', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt, max_iterations: maxIter })
        });

        if (response.ok) {
            const data = await response.json();
            showToast(`Task created: ${data.task_id}`, 'success');
            closeModal('task-modal');
            document.getElementById('task-form').reset();
            fetchTasks();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Failed to create task', 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

async function pauseTask(taskId) {
    try {
        const response = await fetch(`/api/tasks/${taskId}/pause`, { method: 'POST' });
        if (response.ok) {
            showToast('Task paused', 'success');
            fetchTasks();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Failed to pause task', 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

async function resumeTask(taskId) {
    try {
        const response = await fetch(`/api/tasks/${taskId}/resume`, { method: 'POST' });
        if (response.ok) {
            showToast('Task resumed', 'success');
            fetchTasks();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Failed to resume task', 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

async function createMetaPost(event) {
    event.preventDefault();
    const platform = document.getElementById('meta-platform').value;
    const content = document.getElementById('meta-content').value;

    try {
        const response = await fetch('/api/social/meta', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ platform, content })
        });

        if (response.ok) {
            showToast('Meta post created', 'success');
            closeModal('meta-modal');
            document.getElementById('meta-form').reset();
            fetchMetaPosts();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Failed to create post', 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

async function publishMetaPost(postId) {
    try {
        const response = await fetch(`/api/social/meta/${postId}/publish`, { method: 'POST' });
        if (response.ok) {
            showToast('Meta post published', 'success');
            fetchMetaPosts();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Meta API not connected', 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

async function createTweet(event) {
    event.preventDefault();
    const content = document.getElementById('tweet-content').value;

    try {
        const response = await fetch('/api/social/twitter', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content })
        });

        if (response.ok) {
            showToast('Tweet created', 'success');
            closeModal('tweet-modal');
            document.getElementById('tweet-form').reset();
            updateTweetCharCount();
            fetchTweets();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Failed to create tweet', 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

async function publishTweet(tweetId) {
    try {
        const response = await fetch(`/api/social/twitter/${tweetId}/publish`, { method: 'POST' });
        if (response.ok) {
            showToast('Tweet published', 'success');
            fetchTweets();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Twitter API not connected', 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

async function generateBriefing() {
    showToast('Generating CEO briefing...', 'info');

    try {
        const response = await fetch('/api/briefings/generate', { method: 'POST' });
        if (response.ok) {
            const data = await response.json();
            showToast('CEO briefing generated', 'success');
            fetchBriefings();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Failed to generate briefing', 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

async function searchCorrelations() {
    const query = document.getElementById('search-query').value.trim();
    if (!query) return;

    const container = document.getElementById('search-results');
    if (!container) return;
    container.innerHTML = '<div class="loading">Searching...</div>';

    try {
        const response = await fetch(`/api/correlations/search?q=${encodeURIComponent(query)}`);
        const data = await response.json();

        if (data.count === 0) {
            container.innerHTML = '<div class="empty-state">No results found</div>';
            return;
        }

        container.innerHTML = data.results.map(r => `
            <div class="search-result">
                <div class="result-header">
                    <span class="result-folder">${escapeHtml(r.folder)}</span>
                    <span class="result-file">${escapeHtml(r.file)}</span>
                </div>
                <div class="result-preview">${escapeHtml(r.preview)}</div>
            </div>
        `).join('');
    } catch (error) {
        container.innerHTML = '<div class="empty-state">Search error</div>';
    }
}

// =========================================
// Utility functions
// =========================================

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(isoString) {
    if (!isoString) return 'N/A';
    const date = new Date(isoString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// Refresh all data (Bronze + Silver + Gold)
function refreshAll() {
    updateTimestamp();
    fetchStatus();
    fetchApprovals();
    fetchSchedules();
    fetchPlans();
    // Gold tier
    fetchTasks();
    fetchBriefings();
    fetchMetaPosts();
    fetchTweets();
    fetchInvoices();
    fetchHealth();
    fetchAuditLog();
}

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    updateTimestamp();
    setInterval(updateTimestamp, 1000);

    // Initial fetch
    refreshAll();

    // Auto-refresh every 30 seconds
    setInterval(refreshAll, 30000);
});
