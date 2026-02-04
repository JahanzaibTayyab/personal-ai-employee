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

    // Note: Plan creation would typically trigger Claude reasoning loop
    // For now, show a message indicating this needs CLI/Agent interaction
    showToast('Plan creation requires Claude Agent. Use /create-plan skill.', 'info');
    closeModal('plan-modal');
}

function runProcessInbox() {
    // Note: This would trigger the inbox processing workflow
    showToast('Inbox processing requires Claude Agent. Use /process-inbox skill.', 'info');
}

// Utility functions
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

// Refresh all data
function refreshAll() {
    updateTimestamp();
    fetchStatus();
    fetchApprovals();
    fetchSchedules();
    fetchPlans();
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
