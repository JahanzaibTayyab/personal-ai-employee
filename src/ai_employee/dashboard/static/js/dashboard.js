/**
 * AI Employee Dashboard — Obsidian Command
 * Tab navigation, detail modals, real-time data
 */

/* ═══════════════════════════════════════════
   UTILITIES
   ═══════════════════════════════════════════ */

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(isoString) {
    if (!isoString) return 'N/A';
    const d = new Date(isoString);
    return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function renderMarkdown(md) {
    if (!md) return '';
    return md
        .replace(/^#### (.+)$/gm, '<h4>$1</h4>')
        .replace(/^### (.+)$/gm, '<h3>$1</h3>')
        .replace(/^## (.+)$/gm, '<h2>$1</h2>')
        .replace(/^# (.+)$/gm, '<h2>$1</h2>')
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/^---$/gm, '<hr>')
        .replace(/^- (.+)$/gm, '<li>$1</li>')
        .replace(/^(\d+)\. (.+)$/gm, '<li>$2</li>')
        .replace(/(<li>.*<\/li>\n?)+/g, function(match) {
            return '<ul>' + match + '</ul>';
        })
        .replace(/\n{2,}/g, '</p><p>')
        .replace(/^(?!<[hul]|<hr|<li|<\/p>|<p>)(.+)$/gm, '<p>$1</p>')
        .replace(/<p><\/p>/g, '');
}

function updateTimestamp() {
    const now = new Date();
    const ts = now.toISOString().replace('T', ' ').substring(0, 19);
    const el = document.getElementById('timestamp');
    if (el) el.textContent = ts + ' UTC';
}

/* ═══════════════════════════════════════════
   TOAST
   ═══════════════════════════════════════════ */

function showToast(message, type) {
    type = type || 'success';
    const toast = document.getElementById('toast');
    if (!toast) return;
    toast.textContent = message;
    toast.className = 'toast show ' + type;
    setTimeout(function() { toast.className = 'toast'; }, 3000);
}

/* ═══════════════════════════════════════════
   TAB NAVIGATION
   ═══════════════════════════════════════════ */

function initTabs() {
    var triggers = document.querySelectorAll('.tab-trigger');
    triggers.forEach(function(btn) {
        btn.addEventListener('click', function() {
            switchTab(btn.getAttribute('data-tab'));
        });
    });
}

function switchTab(tabName) {
    document.querySelectorAll('.tab-trigger').forEach(function(btn) {
        btn.classList.toggle('active', btn.getAttribute('data-tab') === tabName);
    });
    document.querySelectorAll('.tab-content').forEach(function(panel) {
        panel.classList.toggle('active', panel.id === 'tab-' + tabName);
    });
}

/* ═══════════════════════════════════════════
   ACTION MODALS (create forms)
   ═══════════════════════════════════════════ */

function openModal(modalId) {
    var modal = document.getElementById(modalId);
    if (modal) modal.classList.add('active');
}

function closeModal(modalId) {
    var modal = document.getElementById(modalId);
    if (modal) modal.classList.remove('active');
}

/* ═══════════════════════════════════════════
   DETAIL MODAL (reusable)
   ═══════════════════════════════════════════ */

function openDetailModal(title, bodyHtml, footerHtml, wide) {
    document.getElementById('detail-modal-title').textContent = title;
    document.getElementById('detail-modal-body').innerHTML = bodyHtml;
    document.getElementById('detail-modal-footer').innerHTML = footerHtml || '';
    var content = document.getElementById('detail-modal-content');
    if (wide) {
        content.classList.add('modal-content--wide');
    } else {
        content.classList.remove('modal-content--wide');
    }
    document.getElementById('detail-modal').classList.add('active');
}

function closeDetailModal() {
    document.getElementById('detail-modal').classList.remove('active');
}

/* ── Plan Detail ── */

function showPlanDetail(planId) {
    openDetailModal('Plan Details', '<div class="loading">Loading plan...</div>', '', true);
    fetch('/api/plans/' + encodeURIComponent(planId))
        .then(function(r) { return r.json(); })
        .then(function(plan) {
            var statusBadge = plan.status === 'completed'
                ? '<span class="badge badge--success">Completed</span>'
                : plan.status === 'active'
                    ? '<span class="badge badge--accent">Active</span>'
                    : '<span class="badge badge--neutral">' + escapeHtml(plan.status) + '</span>';

            var pctClass = plan.progress < 30 ? 'low' : plan.progress < 70 ? 'mid' : 'high';

            var stepsHtml = '<ul class="step-list">';
            (plan.steps || []).forEach(function(s) {
                var iconClass = s.status === 'completed' ? 'done'
                    : s.status === 'in_progress' ? 'active'
                    : s.status === 'failed' ? 'failed'
                    : 'pending';
                var iconChar = s.status === 'completed' ? '&#10003;'
                    : s.status === 'in_progress' ? '&#9654;'
                    : s.status === 'failed' ? '!'
                    : '&#9675;';
                var textClass = s.status === 'completed' ? ' done' : '';
                stepsHtml += '<li>'
                    + '<span class="step-icon ' + iconClass + '">' + iconChar + '</span>'
                    + '<span class="step-text' + textClass + '">' + escapeHtml(s.description) + '</span>'
                    + '</li>';
            });
            stepsHtml += '</ul>';

            var body = ''
                + '<div class="detail-section">'
                + '  <div class="detail-grid">'
                + '    <div class="detail-pair"><span class="k">Objective</span><span class="v">' + escapeHtml(plan.objective) + '</span></div>'
                + '    <div class="detail-pair"><span class="k">Status</span><span class="v">' + statusBadge + '</span></div>'
                + '    <div class="detail-pair"><span class="k">Created</span><span class="v">' + formatDate(plan.created_at) + '</span></div>'
                + '    <div class="detail-pair"><span class="k">Progress</span><span class="v">' + plan.steps_completed + '/' + plan.steps_total + ' steps (' + plan.progress + '%)</span></div>'
                + '  </div>'
                + '</div>'
                + '<div class="detail-section">'
                + '  <div class="progress"><div class="progress-fill" data-pct="' + pctClass + '" style="width:' + plan.progress + '%"></div></div>'
                + '</div>'
                + '<div class="detail-section">'
                + '  <div class="detail-label">Steps</div>'
                + '  ' + stepsHtml
                + '</div>';

            if (plan.completion_summary) {
                body += '<div class="detail-section"><div class="detail-label">Completion Summary</div><div class="detail-value">' + escapeHtml(plan.completion_summary) + '</div></div>';
            }

            document.getElementById('detail-modal-body').innerHTML = body;
        })
        .catch(function() {
            document.getElementById('detail-modal-body').innerHTML = '<div class="empty-state">Failed to load plan details</div>';
        });
}

/* ── Briefing Detail ── */

function showBriefingDetail(filename) {
    openDetailModal('CEO Briefing', '<div class="loading">Loading briefing...</div>', '', true);
    fetch('/api/briefings/' + encodeURIComponent(filename))
        .then(function(r) { return r.json(); })
        .then(function(data) {
            var body = ''
                + '<div class="detail-section">'
                + '  <div class="detail-grid">'
                + '    <div class="detail-pair"><span class="k">File</span><span class="v">' + escapeHtml(data.filename) + '</span></div>'
                + '    <div class="detail-pair"><span class="k">Period</span><span class="v">' + escapeHtml(data.period) + '</span></div>'
                + '    <div class="detail-pair"><span class="k">Generated</span><span class="v">' + escapeHtml(String(data.generated)) + '</span></div>'
                + '  </div>'
                + '</div>'
                + '<div class="detail-section">'
                + '  <div class="md-content">' + renderMarkdown(data.content || '') + '</div>'
                + '</div>';
            document.getElementById('detail-modal-body').innerHTML = body;
        })
        .catch(function() {
            document.getElementById('detail-modal-body').innerHTML = '<div class="empty-state">Failed to load briefing</div>';
        });
}

/* ── Task Detail ── */

function showTaskDetail(task) {
    var statusBadge = task.status === 'running'
        ? '<span class="badge badge--accent">Running</span>'
        : task.status === 'paused'
            ? '<span class="badge badge--warning">Paused</span>'
            : task.status === 'completed'
                ? '<span class="badge badge--success">Completed</span>'
                : '<span class="badge badge--neutral">' + escapeHtml(task.status || 'unknown') + '</span>';

    var pct = task.max_iterations ? Math.round((task.iteration / task.max_iterations) * 100) : 0;
    var pctClass = pct < 30 ? 'low' : pct < 70 ? 'mid' : 'high';

    var body = ''
        + '<div class="detail-section">'
        + '  <div class="detail-grid">'
        + '    <div class="detail-pair"><span class="k">Status</span><span class="v">' + statusBadge + '</span></div>'
        + '    <div class="detail-pair"><span class="k">Iteration</span><span class="v">' + (task.iteration || 0) + ' / ' + (task.max_iterations || '?') + '</span></div>'
        + '    <div class="detail-pair"><span class="k">Created</span><span class="v">' + formatDate(task.created_at) + '</span></div>'
        + '    <div class="detail-pair"><span class="k">Task ID</span><span class="v" style="font-family:var(--mono);font-size:.75rem">' + escapeHtml(task.id) + '</span></div>'
        + '  </div>'
        + '</div>'
        + '<div class="detail-section">'
        + '  <div class="progress"><div class="progress-fill" data-pct="' + pctClass + '" style="width:' + pct + '%"></div></div>'
        + '</div>'
        + '<div class="detail-section">'
        + '  <div class="detail-label">Prompt</div>'
        + '  <div class="detail-value"><pre>' + escapeHtml(task.prompt || '') + '</pre></div>'
        + '</div>';

    var footer = '';
    if (task.status === 'running') {
        footer = '<button class="btn btn--warning btn--sm" onclick="pauseTask(\'' + escapeHtml(task.id) + '\'); closeDetailModal();">Pause</button>';
    } else if (task.status === 'paused') {
        footer = '<button class="btn btn--primary btn--sm" onclick="resumeTask(\'' + escapeHtml(task.id) + '\'); closeDetailModal();">Resume</button>';
    }

    openDetailModal('Task Details', body, footer);
}

/* ── Approval Detail ── */

function showApprovalDetail(approval) {
    var catBadge = approval.category === 'email'
        ? '<span class="badge badge--info">Email</span>'
        : approval.category === 'social_post'
            ? '<span class="badge badge--accent">Social Post</span>'
            : '<span class="badge badge--neutral">' + escapeHtml(approval.category) + '</span>';

    var body = ''
        + '<div class="detail-section">'
        + '  <div class="detail-grid">'
        + '    <div class="detail-pair"><span class="k">Category</span><span class="v">' + catBadge + '</span></div>'
        + '    <div class="detail-pair"><span class="k">Created</span><span class="v">' + formatDate(approval.created_at) + '</span></div>'
        + '    <div class="detail-pair"><span class="k">Expires</span><span class="v">' + (approval.expires_at ? formatDate(approval.expires_at) : 'Never') + '</span></div>'
        + '    <div class="detail-pair"><span class="k">ID</span><span class="v" style="font-family:var(--mono);font-size:.72rem">' + escapeHtml(approval.id) + '</span></div>'
        + '  </div>'
        + '</div>';

    if (approval.summary) {
        body += '<div class="detail-section"><div class="detail-label">Summary</div><div class="detail-value">' + escapeHtml(approval.summary) + '</div></div>';
    }

    if (approval.payload) {
        var p = approval.payload;
        if (approval.category === 'email') {
            body += '<div class="detail-section"><div class="detail-label">Email Details</div><div class="detail-grid">'
                + '<div class="detail-pair"><span class="k">To</span><span class="v">' + escapeHtml((p.to || []).join(', ')) + '</span></div>'
                + '<div class="detail-pair"><span class="k">CC</span><span class="v">' + escapeHtml((p.cc || []).join(', ') || 'None') + '</span></div>'
                + '<div class="detail-pair"><span class="k">Subject</span><span class="v">' + escapeHtml(p.subject || '') + '</span></div>'
                + '</div></div>'
                + '<div class="detail-section"><div class="detail-label">Body</div><div class="detail-value"><pre>' + escapeHtml(p.body || '') + '</pre></div></div>';
        } else {
            body += '<div class="detail-section"><div class="detail-label">Content</div><div class="detail-value"><pre>' + escapeHtml(p.content || JSON.stringify(p, null, 2)) + '</pre></div></div>';
        }
    }

    var footer = '';
    if (!approval.is_expired) {
        footer = '<button class="btn btn--danger btn--sm" onclick="rejectRequest(\'' + escapeHtml(approval.id) + '\'); closeDetailModal();">Reject</button>'
            + '<button class="btn btn--primary btn--sm" onclick="approveRequest(\'' + escapeHtml(approval.id) + '\'); closeDetailModal();">Approve</button>';
    }

    openDetailModal('Approval Request', body, footer, true);
}

/* ── Meta Post Detail ── */

function showMetaPostDetail(post) {
    var statusBadge = post.status === 'draft'
        ? '<span class="badge badge--warning">Draft</span>'
        : post.status === 'published'
            ? '<span class="badge badge--success">Published</span>'
            : '<span class="badge badge--neutral">' + escapeHtml(post.status || 'draft') + '</span>';

    var body = ''
        + '<div class="detail-section">'
        + '  <div class="detail-grid">'
        + '    <div class="detail-pair"><span class="k">Platform</span><span class="v"><span class="badge badge--accent">' + escapeHtml((post.platform || '').toUpperCase()) + '</span></span></div>'
        + '    <div class="detail-pair"><span class="k">Status</span><span class="v">' + statusBadge + '</span></div>'
        + '    <div class="detail-pair"><span class="k">Created</span><span class="v">' + formatDate(post.created_at) + '</span></div>'
        + (post.posted_time ? '    <div class="detail-pair"><span class="k">Posted</span><span class="v">' + formatDate(post.posted_time) + '</span></div>' : '')
        + '  </div>'
        + '</div>'
        + '<div class="detail-section">'
        + '  <div class="detail-label">Content</div>'
        + '  <div class="detail-value"><pre>' + escapeHtml(post.content || '') + '</pre></div>'
        + '</div>';

    var footer = '';
    if (post.status === 'draft') {
        footer = '<button class="btn btn--primary btn--sm" onclick="publishMetaPost(\'' + escapeHtml(post.id) + '\'); closeDetailModal();">Publish</button>';
    }

    openDetailModal('Meta Post', body, footer);
}

/* ── Tweet Detail ── */

function showTweetDetail(tweet) {
    var statusBadge = tweet.status === 'draft'
        ? '<span class="badge badge--warning">Draft</span>'
        : tweet.status === 'published'
            ? '<span class="badge badge--success">Published</span>'
            : '<span class="badge badge--neutral">' + escapeHtml(tweet.status || 'draft') + '</span>';

    var body = ''
        + '<div class="detail-section">'
        + '  <div class="detail-grid">'
        + '    <div class="detail-pair"><span class="k">Status</span><span class="v">' + statusBadge + '</span></div>'
        + '    <div class="detail-pair"><span class="k">Created</span><span class="v">' + formatDate(tweet.created_at) + '</span></div>'
        + (tweet.is_thread ? '    <div class="detail-pair"><span class="k">Thread</span><span class="v">Yes</span></div>' : '')
        + (tweet.posted_time ? '    <div class="detail-pair"><span class="k">Posted</span><span class="v">' + formatDate(tweet.posted_time) + '</span></div>' : '')
        + '  </div>'
        + '</div>'
        + '<div class="detail-section">'
        + '  <div class="detail-label">Content</div>'
        + '  <div class="detail-value"><pre>' + escapeHtml(tweet.content || '') + '</pre></div>'
        + '</div>';

    var footer = '';
    if (tweet.status === 'draft') {
        footer = '<button class="btn btn--primary btn--sm" onclick="publishTweet(\'' + escapeHtml(tweet.id) + '\'); closeDetailModal();">Publish</button>';
    }

    openDetailModal('Tweet', body, footer);
}

/* ── Invoice Detail ── */

function showInvoiceDetail(inv) {
    var statusBadge = inv.status === 'paid'
        ? '<span class="badge badge--success">Paid</span>'
        : inv.status === 'overdue'
            ? '<span class="badge badge--danger">Overdue</span>'
            : '<span class="badge badge--warning">' + escapeHtml(inv.status || 'draft') + '</span>';

    var body = '<div class="detail-section"><div class="detail-grid">'
        + '<div class="detail-pair"><span class="k">Customer</span><span class="v">' + escapeHtml(inv.customer || 'Unknown') + '</span></div>'
        + '<div class="detail-pair"><span class="k">Amount</span><span class="v">$' + (inv.amount || 0) + '</span></div>'
        + '<div class="detail-pair"><span class="k">Status</span><span class="v">' + statusBadge + '</span></div>'
        + '<div class="detail-pair"><span class="k">Date</span><span class="v">' + escapeHtml(inv.date || 'N/A') + '</span></div>'
        + (inv.due_date ? '<div class="detail-pair"><span class="k">Due Date</span><span class="v">' + escapeHtml(inv.due_date) + '</span></div>' : '')
        + '</div></div>';

    openDetailModal('Invoice', body, '');
}

/* ── Audit Detail ── */

function showAuditDetail(entry) {
    var body = '<div class="detail-section"><div class="detail-label">Audit Entry</div>'
        + '<div class="detail-value"><pre>' + escapeHtml(JSON.stringify(entry, null, 2)) + '</pre></div></div>';
    openDetailModal('Audit Entry', body, '');
}

/* ── Search Result Detail ── */

function showSearchResultDetail(result) {
    var body = '<div class="detail-section"><div class="detail-grid">'
        + '<div class="detail-pair"><span class="k">File</span><span class="v">' + escapeHtml(result.file) + '</span></div>'
        + '<div class="detail-pair"><span class="k">Folder</span><span class="v"><span class="badge badge--accent">' + escapeHtml(result.folder) + '</span></span></div>'
        + (result.id ? '<div class="detail-pair"><span class="k">ID</span><span class="v">' + escapeHtml(result.id) + '</span></div>' : '')
        + '</div></div>'
        + '<div class="detail-section"><div class="detail-label">Preview</div><div class="detail-value"><pre>' + escapeHtml(result.preview || '') + '</pre></div></div>';

    if (result.match_context) {
        body += '<div class="detail-section"><div class="detail-label">Match Context</div><div class="detail-value"><pre>' + escapeHtml(result.match_context) + '</pre></div></div>';
    }

    openDetailModal('Search Result', body, '', true);
}

/* ═══════════════════════════════════════════
   KEYBOARD & BACKDROP CLOSE
   ═══════════════════════════════════════════ */

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        /* Close detail modal first, then action modals */
        var detail = document.getElementById('detail-modal');
        if (detail && detail.classList.contains('active')) {
            closeDetailModal();
            return;
        }
        document.querySelectorAll('.modal.active').forEach(function(m) {
            m.classList.remove('active');
        });
    }
});

/* ═══════════════════════════════════════════
   FETCH — STATUS
   ═══════════════════════════════════════════ */

function updateWatcherStatus(dotId, labelId, status) {
    var dot = document.getElementById(dotId);
    var label = document.getElementById(labelId);
    if (dot) {
        dot.className = 'dot' + (status === 'running' ? ' running' : '');
    }
    if (label) {
        label.textContent = status;
    }
}

async function fetchStatus() {
    try {
        var response = await fetch('/api/status');
        var data = await response.json();

        var el;
        el = document.getElementById('inbox-count');
        if (el) el.textContent = data.counts.inbox;
        el = document.getElementById('needs-action-count');
        if (el) el.textContent = data.counts.needs_action;
        el = document.getElementById('done-count');
        if (el) el.textContent = data.counts.done;
        el = document.getElementById('quarantine-count');
        if (el) el.textContent = data.counts.quarantine;

        updateWatcherStatus('file-watcher-dot', 'file-watcher-label', data.watchers.file);
        updateWatcherStatus('gmail-watcher-dot', 'gmail-watcher-label', data.watchers.gmail);
        updateWatcherStatus('whatsapp-watcher-dot', 'whatsapp-watcher-label', data.watchers.whatsapp);
        updateWatcherStatus('approval-watcher-dot', 'approval-watcher-label', data.watchers.approval);
    } catch (err) {
        /* silent */
    }
}

/* ═══════════════════════════════════════════
   FETCH — APPROVALS
   ═══════════════════════════════════════════ */

var _approvalsCache = [];

function getApprovalSummary(approval) {
    if (approval.payload) {
        if (approval.category === 'email') {
            return 'Email to ' + ((approval.payload.to || []).join(', ') || 'N/A') + ': ' + (approval.payload.subject || 'No subject');
        }
        if (approval.category === 'linkedin' || approval.category === 'social_post') {
            var c = approval.payload.content || '';
            return c.substring(0, 100) + (c.length > 100 ? '...' : '');
        }
    }
    return 'Pending approval';
}

async function fetchApprovals() {
    try {
        var response = await fetch('/api/approvals');
        var data = await response.json();
        _approvalsCache = data.approvals || [];

        var badge = document.getElementById('approval-badge');
        if (badge) badge.textContent = data.count;

        var container = document.getElementById('approvals-list');
        if (!container) return;

        if (data.count === 0) {
            container.innerHTML = '<div class="empty-state">No pending approvals</div>';
            return;
        }

        container.innerHTML = data.approvals.map(function(a, idx) {
            var summary = escapeHtml(a.summary || getApprovalSummary(a));
            var catBadge = a.category === 'email'
                ? '<span class="badge badge--info">Email</span>'
                : '<span class="badge badge--accent">' + escapeHtml(a.category) + '</span>';
            return '<div class="list-item" onclick="showApprovalDetail(_approvalsCache[' + idx + '])">'
                + '  <div class="item-main">'
                + '    <div class="item-title">' + summary + '</div>'
                + '    <div class="item-meta">' + catBadge + '<span class="sep">|</span>' + formatDate(a.created_at)
                + (a.is_expired ? ' <span class="badge badge--danger">Expired</span>' : '') + '</div>'
                + '  </div>'
                + '  <div class="item-actions">'
                + '    <button class="btn btn--primary btn--sm" onclick="event.stopPropagation(); approveRequest(\'' + escapeHtml(a.id) + '\')"' + (a.is_expired ? ' disabled' : '') + '>Approve</button>'
                + '    <button class="btn btn--danger btn--sm" onclick="event.stopPropagation(); rejectRequest(\'' + escapeHtml(a.id) + '\')"' + (a.is_expired ? ' disabled' : '') + '>Reject</button>'
                + '  </div>'
                + '</div>';
        }).join('');
    } catch (err) {
        var c = document.getElementById('approvals-list');
        if (c) c.innerHTML = '<div class="empty-state">Error loading approvals</div>';
    }
}

/* ═══════════════════════════════════════════
   FETCH — SCHEDULES
   ═══════════════════════════════════════════ */

async function fetchSchedules() {
    try {
        var response = await fetch('/api/schedules');
        var data = await response.json();

        var badge = document.getElementById('schedule-badge');
        if (badge) badge.textContent = data.count;

        var container = document.getElementById('schedules-list');
        if (!container) return;

        if (data.count === 0) {
            container.innerHTML = '<div class="empty-state">No scheduled tasks</div>';
            return;
        }

        container.innerHTML = data.schedules.map(function(s) {
            var enabledBadge = s.enabled
                ? '<span class="badge badge--success">Enabled</span>'
                : '<span class="badge badge--neutral">Disabled</span>';
            return '<div class="list-item">'
                + '  <div class="item-main">'
                + '    <div class="item-title">' + escapeHtml(s.name) + '</div>'
                + '    <div class="item-meta">'
                + '      <span style="font-family:var(--mono);font-size:.68rem">' + escapeHtml(s.schedule) + '</span>'
                + '      <span class="sep">|</span>' + enabledBadge
                + '    </div>'
                + '  </div>'
                + '</div>';
        }).join('');
    } catch (err) {
        var c = document.getElementById('schedules-list');
        if (c) c.innerHTML = '<div class="empty-state">Error loading schedules</div>';
    }
}

/* ═══════════════════════════════════════════
   FETCH — PLANS
   ═══════════════════════════════════════════ */

async function fetchPlans() {
    try {
        var response = await fetch('/api/plans');
        var data = await response.json();

        var badge = document.getElementById('plan-badge');
        if (badge) badge.textContent = data.count;

        var container = document.getElementById('plans-list');
        if (!container) return;

        if (data.count === 0) {
            container.innerHTML = '<div class="empty-state">No active plans</div>';
            return;
        }

        container.innerHTML = data.plans.map(function(p) {
            var statusBadge = p.status === 'completed'
                ? '<span class="badge badge--success">Completed</span>'
                : p.status === 'active'
                    ? '<span class="badge badge--accent">Active</span>'
                    : '<span class="badge badge--neutral">' + escapeHtml(p.status) + '</span>';
            var pctClass = p.progress < 30 ? 'low' : p.progress < 70 ? 'mid' : 'high';
            return '<div class="list-item" onclick="showPlanDetail(\'' + escapeHtml(p.id) + '\')">'
                + '  <div class="item-main">'
                + '    <div class="item-title">' + escapeHtml(p.task) + '</div>'
                + '    <div style="margin:.35rem 0"><div class="progress"><div class="progress-fill" data-pct="' + pctClass + '" style="width:' + p.progress + '%"></div></div></div>'
                + '    <div class="item-meta">' + statusBadge + '<span class="sep">|</span>' + p.steps_completed + '/' + p.steps_total + ' steps<span class="sep">|</span>' + p.progress + '%</div>'
                + '  </div>'
                + '</div>';
        }).join('');
    } catch (err) {
        var c = document.getElementById('plans-list');
        if (c) c.innerHTML = '<div class="empty-state">Error loading plans</div>';
    }
}

/* ═══════════════════════════════════════════
   FETCH — TASKS (Ralph Wiggum)
   ═══════════════════════════════════════════ */

var _tasksCache = [];

async function fetchTasks() {
    try {
        var response = await fetch('/api/tasks');
        var data = await response.json();
        _tasksCache = data.tasks || [];

        var badge = document.getElementById('task-badge');
        if (badge) badge.textContent = data.count;

        var container = document.getElementById('tasks-list');
        if (!container) return;

        if (data.count === 0) {
            container.innerHTML = '<div class="empty-state">No active tasks</div>';
            return;
        }

        container.innerHTML = data.tasks.map(function(t, idx) {
            var statusBadge = t.status === 'running'
                ? '<span class="badge badge--accent">Running</span>'
                : t.status === 'paused'
                    ? '<span class="badge badge--warning">Paused</span>'
                    : t.status === 'completed'
                        ? '<span class="badge badge--success">Completed</span>'
                        : '<span class="badge badge--neutral">' + escapeHtml(t.status || 'unknown') + '</span>';
            var prompt = escapeHtml((t.prompt || '').substring(0, 80)) + ((t.prompt || '').length > 80 ? '...' : '');
            return '<div class="list-item" onclick="showTaskDetail(_tasksCache[' + idx + '])">'
                + '  <div class="item-main">'
                + '    <div class="item-title">' + prompt + '</div>'
                + '    <div class="item-meta">' + statusBadge + '<span class="sep">|</span>Iter ' + (t.iteration || 0) + '/' + (t.max_iterations || '?') + '</div>'
                + '  </div>'
                + '  <div class="item-actions">'
                + (t.status === 'running' ? '<button class="btn btn--secondary btn--sm" onclick="event.stopPropagation(); pauseTask(\'' + escapeHtml(t.id) + '\')">Pause</button>' : '')
                + (t.status === 'paused' ? '<button class="btn btn--primary btn--sm" onclick="event.stopPropagation(); resumeTask(\'' + escapeHtml(t.id) + '\')">Resume</button>' : '')
                + '  </div>'
                + '</div>';
        }).join('');
    } catch (err) {
        var c = document.getElementById('tasks-list');
        if (c) c.innerHTML = '<div class="empty-state">Error loading tasks</div>';
    }
}

/* ═══════════════════════════════════════════
   FETCH — BRIEFINGS
   ═══════════════════════════════════════════ */

async function fetchBriefings() {
    try {
        var response = await fetch('/api/briefings');
        var data = await response.json();

        var badge = document.getElementById('briefing-badge');
        if (badge) badge.textContent = data.count;

        var container = document.getElementById('briefings-list');
        if (!container) return;

        if (data.count === 0) {
            container.innerHTML = '<div class="empty-state">No briefings generated yet</div>';
            return;
        }

        container.innerHTML = data.briefings.map(function(b) {
            return '<div class="list-item" onclick="showBriefingDetail(\'' + escapeHtml(b.filename) + '\')">'
                + '  <div class="item-main">'
                + '    <div class="item-title">' + escapeHtml(b.filename) + '</div>'
                + '    <div class="item-desc">' + escapeHtml(b.preview) + '</div>'
                + '    <div class="item-meta">'
                + (b.period ? escapeHtml(b.period) : '')
                + (b.generated ? '<span class="sep">|</span>' + formatDate(b.generated) : '')
                + '    </div>'
                + '  </div>'
                + '</div>';
        }).join('');
    } catch (err) {
        var c = document.getElementById('briefings-list');
        if (c) c.innerHTML = '<div class="empty-state">Error loading briefings</div>';
    }
}

/* ═══════════════════════════════════════════
   FETCH — META POSTS
   ═══════════════════════════════════════════ */

var _metaCache = [];

async function fetchMetaPosts() {
    try {
        var response = await fetch('/api/social/meta');
        var data = await response.json();
        _metaCache = data.posts || [];

        var badge = document.getElementById('meta-badge');
        if (badge) badge.textContent = data.count;

        var container = document.getElementById('meta-list');
        if (!container) return;

        if (data.count === 0) {
            container.innerHTML = '<div class="empty-state">No Meta posts yet</div>';
            return;
        }

        container.innerHTML = data.posts.map(function(post, idx) {
            var statusBadge = post.status === 'draft'
                ? '<span class="badge badge--warning">Draft</span>'
                : '<span class="badge badge--success">Published</span>';
            var preview = escapeHtml((post.content || '').substring(0, 120)) + ((post.content || '').length > 120 ? '...' : '');
            return '<div class="list-item" onclick="showMetaPostDetail(_metaCache[' + idx + '])">'
                + '  <div class="item-main">'
                + '    <div class="item-title">' + preview + '</div>'
                + '    <div class="item-meta"><span class="badge badge--accent">' + escapeHtml((post.platform || '').toUpperCase()) + '</span><span class="sep">|</span>' + statusBadge + '</div>'
                + '  </div>'
                + (post.status === 'draft' ? '  <div class="item-actions"><button class="btn btn--primary btn--sm" onclick="event.stopPropagation(); publishMetaPost(\'' + escapeHtml(post.id) + '\')">Publish</button></div>' : '')
                + '</div>';
        }).join('');
    } catch (err) {
        var c = document.getElementById('meta-list');
        if (c) c.innerHTML = '<div class="empty-state">Error loading Meta posts</div>';
    }
}

/* ═══════════════════════════════════════════
   FETCH — TWEETS
   ═══════════════════════════════════════════ */

var _tweetsCache = [];

async function fetchTweets() {
    try {
        var response = await fetch('/api/social/twitter');
        var data = await response.json();
        _tweetsCache = data.tweets || [];

        var badge = document.getElementById('twitter-badge');
        if (badge) badge.textContent = data.count;

        var container = document.getElementById('twitter-list');
        if (!container) return;

        if (data.count === 0) {
            container.innerHTML = '<div class="empty-state">No tweets yet</div>';
            return;
        }

        container.innerHTML = data.tweets.map(function(tw, idx) {
            var statusBadge = tw.status === 'draft'
                ? '<span class="badge badge--warning">Draft</span>'
                : '<span class="badge badge--success">Published</span>';
            return '<div class="list-item" onclick="showTweetDetail(_tweetsCache[' + idx + '])">'
                + '  <div class="item-main">'
                + '    <div class="item-title">' + escapeHtml((tw.content || '').substring(0, 120)) + '</div>'
                + '    <div class="item-meta">' + statusBadge
                + (tw.is_thread ? '<span class="sep">|</span>Thread' : '')
                + (tw.posted_time ? '<span class="sep">|</span>' + formatDate(tw.posted_time) : '')
                + '    </div>'
                + '  </div>'
                + (tw.status === 'draft' ? '  <div class="item-actions"><button class="btn btn--primary btn--sm" onclick="event.stopPropagation(); publishTweet(\'' + escapeHtml(tw.id) + '\')">Publish</button></div>' : '')
                + '</div>';
        }).join('');
    } catch (err) {
        var c = document.getElementById('twitter-list');
        if (c) c.innerHTML = '<div class="empty-state">Error loading tweets</div>';
    }
}

/* ═══════════════════════════════════════════
   FETCH — INVOICES
   ═══════════════════════════════════════════ */

var _invoicesCache = [];

async function fetchInvoices() {
    try {
        var response = await fetch('/api/invoices');
        var data = await response.json();
        _invoicesCache = data.invoices || [];

        var badge = document.getElementById('invoice-badge');
        if (badge) badge.textContent = data.count;

        var container = document.getElementById('invoices-list');
        if (!container) return;

        if (data.count === 0) {
            container.innerHTML = '<div class="empty-state">No invoices</div>';
            return;
        }

        container.innerHTML = data.invoices.map(function(inv, idx) {
            var statusBadge = inv.status === 'paid'
                ? '<span class="badge badge--success">Paid</span>'
                : inv.status === 'overdue'
                    ? '<span class="badge badge--danger">Overdue</span>'
                    : '<span class="badge badge--warning">' + escapeHtml(inv.status || 'draft') + '</span>';
            return '<div class="list-item" onclick="showInvoiceDetail(_invoicesCache[' + idx + '])">'
                + '  <div class="item-main">'
                + '    <div class="item-title">' + escapeHtml(inv.customer || 'Unknown') + '</div>'
                + '    <div class="item-meta">$' + (inv.amount || 0) + '<span class="sep">|</span>' + statusBadge
                + (inv.due_date ? '<span class="sep">|</span>Due: ' + escapeHtml(inv.due_date) : '') + '</div>'
                + '  </div>'
                + '</div>';
        }).join('');
    } catch (err) {
        var c = document.getElementById('invoices-list');
        if (c) c.innerHTML = '<div class="empty-state">No invoices</div>';
    }
}

/* ═══════════════════════════════════════════
   FETCH — HEALTH
   ═══════════════════════════════════════════ */

async function fetchHealth() {
    try {
        var response = await fetch('/api/health');
        var data = await response.json();

        var container = document.getElementById('health-status');
        if (!container) return;

        var bannerClass = data.overall === 'healthy' ? 'healthy' : 'degraded';
        var services = data.services || {};

        var html = '<div class="health-banner ' + bannerClass + '">'
            + 'System: ' + escapeHtml((data.overall || 'unknown'))
            + (data.dev_mode ? ' <span class="dev-badge">DEV MODE</span>' : '')
            + '</div>';

        Object.entries(services).forEach(function(entry) {
            var name = entry[0];
            var info = entry[1];
            var dotClass = info.status === 'ok' ? 'ok' : info.status === 'degraded' ? 'warn' : 'off';
            html += '<div class="service-row">'
                + '<span class="service-name">' + escapeHtml(name) + '</span>'
                + '<span><span class="service-dot ' + dotClass + '"></span><span class="service-label">' + escapeHtml(info.status || 'unknown') + '</span></span>'
                + '</div>';
        });

        if (data.summary) {
            html += '<div class="health-footer">' + escapeHtml(data.summary) + '</div>';
        }

        container.innerHTML = html;
    } catch (err) {
        var c = document.getElementById('health-status');
        if (c) c.innerHTML = '<div class="empty-state">Error checking health</div>';
    }
}

/* ═══════════════════════════════════════════
   FETCH — AUDIT LOG
   ═══════════════════════════════════════════ */

var _auditCache = [];

async function fetchAuditLog() {
    try {
        var response = await fetch('/api/audit');
        var data = await response.json();
        _auditCache = data.entries || [];

        var badge = document.getElementById('audit-badge');
        if (badge) badge.textContent = data.count;

        var container = document.getElementById('audit-list');
        if (!container) return;

        if (data.count === 0) {
            container.innerHTML = '<div class="empty-state">No audit entries</div>';
            return;
        }

        container.innerHTML = data.entries.slice(0, 15).map(function(entry, idx) {
            var action = entry.action_type || entry.operation || 'action';
            var result = entry.result || (entry.success ? 'success' : 'failure');
            var resultBadge = result === 'success'
                ? '<span class="badge badge--success">OK</span>'
                : '<span class="badge badge--danger">Fail</span>';
            return '<div class="list-item" onclick="showAuditDetail(_auditCache[' + idx + '])">'
                + '  <div class="item-main">'
                + '    <div class="item-title">' + escapeHtml(action) + '</div>'
                + '    <div class="item-meta"><span style="font-family:var(--mono);font-size:.66rem">' + escapeHtml((entry.timestamp || '').substring(11, 19)) + '</span><span class="sep">|</span>' + resultBadge + '</div>'
                + '  </div>'
                + '</div>';
        }).join('');
    } catch (err) {
        var c = document.getElementById('audit-list');
        if (c) c.innerHTML = '<div class="empty-state">No audit entries</div>';
    }
}

/* ═══════════════════════════════════════════
   ACTION HANDLERS
   ═══════════════════════════════════════════ */

async function approveRequest(approvalId) {
    try {
        var response = await fetch('/api/approvals/' + approvalId + '/approve', { method: 'POST' });
        if (response.ok) {
            showToast('Approval granted', 'success');
            fetchApprovals();
        } else {
            var err = await response.json();
            showToast(err.detail || 'Failed to approve', 'error');
        }
    } catch (e) {
        showToast('Error: ' + e.message, 'error');
    }
}

async function rejectRequest(approvalId) {
    try {
        var response = await fetch('/api/approvals/' + approvalId + '/reject', { method: 'POST' });
        if (response.ok) {
            showToast('Request rejected', 'success');
            fetchApprovals();
        } else {
            var err = await response.json();
            showToast(err.detail || 'Failed to reject', 'error');
        }
    } catch (e) {
        showToast('Error: ' + e.message, 'error');
    }
}

async function sendEmail(event) {
    event.preventDefault();
    var to = document.getElementById('email-to').value;
    var cc = document.getElementById('email-cc').value;
    var subject = document.getElementById('email-subject').value;
    var body = document.getElementById('email-body').value;

    try {
        var response = await fetch('/api/email/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ to: [to], cc: cc ? [cc] : [], subject: subject, body: body })
        });
        if (response.ok) {
            showToast('Email queued for approval', 'success');
            closeModal('email-modal');
            document.getElementById('email-form').reset();
            fetchApprovals();
        } else {
            var err = await response.json();
            showToast(err.detail || 'Failed to send email', 'error');
        }
    } catch (e) {
        showToast('Error: ' + e.message, 'error');
    }
}

async function postLinkedIn(event) {
    event.preventDefault();
    var content = document.getElementById('linkedin-content').value;
    try {
        var response = await fetch('/api/linkedin/post', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: content })
        });
        if (response.ok) {
            showToast('LinkedIn post queued for approval', 'success');
            closeModal('linkedin-modal');
            document.getElementById('linkedin-form').reset();
            updateLinkedInCharCount();
            fetchApprovals();
        } else {
            var err = await response.json();
            showToast(err.detail || 'Failed to create post', 'error');
        }
    } catch (e) {
        showToast('Error: ' + e.message, 'error');
    }
}

async function createPlan(event) {
    event.preventDefault();
    var task = document.getElementById('plan-objective').value;
    var description = document.getElementById('plan-description').value;

    var steps = [];
    if (description) {
        steps = description.split('\n')
            .filter(function(l) { return l.trim(); })
            .map(function(l) { return l.replace(/^\d+[\.\)]\s*/, '').trim(); })
            .filter(function(s) { return s; });
    }

    try {
        var response = await fetch('/api/plans/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ task: task, objective: task, steps: steps.length > 0 ? steps : [task] })
        });
        if (response.ok) {
            var data = await response.json();
            showToast('Plan created: ' + data.plan_id + ' (' + data.steps_count + ' steps)', 'success');
            closeModal('plan-modal');
            document.getElementById('plan-form').reset();
            fetchPlans();
        } else {
            var err = await response.json();
            showToast(err.detail || 'Failed to create plan', 'error');
        }
    } catch (e) {
        showToast('Error: ' + e.message, 'error');
    }
}

async function runProcessInbox() {
    showToast('Processing inbox...', 'info');
    try {
        var response = await fetch('/api/inbox/process', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ max_items: 5 })
        });
        if (response.ok) {
            var data = await response.json();
            if (data.processed === 0) {
                showToast('No items to process', 'info');
            } else {
                showToast('Processed ' + data.success_count + ' items (' + data.failed_count + ' failed, ' + data.remaining + ' remaining)', 'success');
            }
            fetchStatus();
        } else {
            var err = await response.json();
            showToast(err.detail || 'Failed to process inbox', 'error');
        }
    } catch (e) {
        showToast('Error: ' + e.message, 'error');
    }
}

async function createTask(event) {
    event.preventDefault();
    var prompt = document.getElementById('task-prompt').value;
    var maxIter = parseInt(document.getElementById('task-max-iter').value) || 10;

    try {
        var response = await fetch('/api/tasks', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: prompt, max_iterations: maxIter })
        });
        if (response.ok) {
            var data = await response.json();
            showToast('Task created: ' + data.task_id, 'success');
            closeModal('task-modal');
            document.getElementById('task-form').reset();
            fetchTasks();
        } else {
            var err = await response.json();
            showToast(err.detail || 'Failed to create task', 'error');
        }
    } catch (e) {
        showToast('Error: ' + e.message, 'error');
    }
}

async function pauseTask(taskId) {
    try {
        var response = await fetch('/api/tasks/' + taskId + '/pause', { method: 'POST' });
        if (response.ok) {
            showToast('Task paused', 'success');
            fetchTasks();
        } else {
            var err = await response.json();
            showToast(err.detail || 'Failed to pause task', 'error');
        }
    } catch (e) {
        showToast('Error: ' + e.message, 'error');
    }
}

async function resumeTask(taskId) {
    try {
        var response = await fetch('/api/tasks/' + taskId + '/resume', { method: 'POST' });
        if (response.ok) {
            showToast('Task resumed', 'success');
            fetchTasks();
        } else {
            var err = await response.json();
            showToast(err.detail || 'Failed to resume task', 'error');
        }
    } catch (e) {
        showToast('Error: ' + e.message, 'error');
    }
}

async function createMetaPost(event) {
    event.preventDefault();
    var platform = document.getElementById('meta-platform').value;
    var content = document.getElementById('meta-content').value;

    try {
        var response = await fetch('/api/social/meta', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ platform: platform, content: content })
        });
        if (response.ok) {
            showToast('Meta post created', 'success');
            closeModal('meta-modal');
            document.getElementById('meta-form').reset();
            fetchMetaPosts();
        } else {
            var err = await response.json();
            showToast(err.detail || 'Failed to create post', 'error');
        }
    } catch (e) {
        showToast('Error: ' + e.message, 'error');
    }
}

async function publishMetaPost(postId) {
    try {
        var response = await fetch('/api/social/meta/' + postId + '/publish', { method: 'POST' });
        if (response.ok) {
            showToast('Meta post published', 'success');
            fetchMetaPosts();
        } else {
            var err = await response.json();
            showToast(err.detail || 'Meta API not connected', 'error');
        }
    } catch (e) {
        showToast('Error: ' + e.message, 'error');
    }
}

async function createTweet(event) {
    event.preventDefault();
    var content = document.getElementById('tweet-content').value;
    try {
        var response = await fetch('/api/social/twitter', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: content })
        });
        if (response.ok) {
            showToast('Tweet created', 'success');
            closeModal('tweet-modal');
            document.getElementById('tweet-form').reset();
            updateTweetCharCount();
            fetchTweets();
        } else {
            var err = await response.json();
            showToast(err.detail || 'Failed to create tweet', 'error');
        }
    } catch (e) {
        showToast('Error: ' + e.message, 'error');
    }
}

async function publishTweet(tweetId) {
    try {
        var response = await fetch('/api/social/twitter/' + tweetId + '/publish', { method: 'POST' });
        if (response.ok) {
            showToast('Tweet published', 'success');
            fetchTweets();
        } else {
            var err = await response.json();
            showToast(err.detail || 'Twitter API not connected', 'error');
        }
    } catch (e) {
        showToast('Error: ' + e.message, 'error');
    }
}

async function generateBriefing() {
    showToast('Generating CEO briefing...', 'info');
    try {
        var response = await fetch('/api/briefings/generate', { method: 'POST' });
        if (response.ok) {
            showToast('CEO briefing generated', 'success');
            fetchBriefings();
        } else {
            var err = await response.json();
            showToast(err.detail || 'Failed to generate briefing', 'error');
        }
    } catch (e) {
        showToast('Error: ' + e.message, 'error');
    }
}

async function searchCorrelations() {
    var query = document.getElementById('search-query').value.trim();
    if (!query) return;

    var container = document.getElementById('search-results');
    if (!container) return;
    container.innerHTML = '<div class="loading">Searching...</div>';

    try {
        var response = await fetch('/api/correlations/search?q=' + encodeURIComponent(query));
        var data = await response.json();

        if (data.count === 0) {
            container.innerHTML = '<div class="empty-state">No results found</div>';
            return;
        }

        var _searchCache = data.results;
        window._searchCache = _searchCache;

        container.innerHTML = data.results.map(function(r, idx) {
            return '<div class="list-item" onclick="showSearchResultDetail(window._searchCache[' + idx + '])">'
                + '  <div class="item-main">'
                + '    <div class="item-title">' + escapeHtml(r.file) + '</div>'
                + '    <div class="item-desc">' + escapeHtml(r.preview) + '</div>'
                + '    <div class="item-meta"><span class="badge badge--accent">' + escapeHtml(r.folder) + '</span></div>'
                + '  </div>'
                + '</div>';
        }).join('');
    } catch (err) {
        container.innerHTML = '<div class="empty-state">Search error</div>';
    }
}

/* ═══════════════════════════════════════════
   CHAR COUNTS
   ═══════════════════════════════════════════ */

function updateLinkedInCharCount() {
    var el = document.getElementById('linkedin-content');
    var counter = document.getElementById('linkedin-chars');
    if (el && counter) counter.textContent = el.value.length;
}

function updateTweetCharCount() {
    var el = document.getElementById('tweet-content');
    var counter = document.getElementById('tweet-chars');
    if (el && counter) counter.textContent = el.value.length;
}

/* ═══════════════════════════════════════════
   REFRESH ALL
   ═══════════════════════════════════════════ */

function refreshAll() {
    updateTimestamp();
    fetchStatus();
    fetchApprovals();
    fetchSchedules();
    fetchPlans();
    fetchTasks();
    fetchBriefings();
    fetchMetaPosts();
    fetchTweets();
    fetchInvoices();
    fetchHealth();
    fetchAuditLog();
}

/* ═══════════════════════════════════════════
   INIT
   ═══════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', function() {
    /* Initialize Lucide icons */
    if (window.lucide) lucide.createIcons();

    initTabs();
    updateTimestamp();
    setInterval(updateTimestamp, 1000);

    /* Char count listeners */
    var li = document.getElementById('linkedin-content');
    if (li) li.addEventListener('input', updateLinkedInCharCount);
    var tw = document.getElementById('tweet-content');
    if (tw) tw.addEventListener('input', updateTweetCharCount);

    refreshAll();
    setInterval(refreshAll, 30000);
});
