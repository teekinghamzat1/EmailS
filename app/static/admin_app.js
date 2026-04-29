document.addEventListener('DOMContentLoaded', () => {
    
    // Elements
    const elDomains      = document.getElementById('metric-domains');
    const elCompleted    = document.getElementById('metric-completed');
    const elValidMails   = document.getElementById('metric-valid-emails');
    const elPatternMails = document.getElementById('metric-pattern-emails');
    const elTableBody    = document.getElementById('table-body');
    const btnExport      = document.getElementById('btn-export');

    // Settings Elements
    const switchMaster   = document.getElementById('master-switch');
    const elMasterStatus = document.getElementById('master-status');
    const inputMonthly   = document.getElementById('input-monthly-limit');
    const inputDaily     = document.getElementById('input-daily-limit');
    const btnSave        = document.getElementById('btn-save-settings');
    const elQuotaMonthlyText = document.getElementById('quota-monthly-text');
    const elQuotaDailyText   = document.getElementById('quota-daily-text');
    const progressMonthly    = document.getElementById('progress-monthly');
    const progressDaily      = document.getElementById('progress-daily');

    const formatNum = (num) => new Intl.NumberFormat('en-US').format(num ?? 0);

    async function fetchSettings() {
        try {
            const response = await fetch('/admin/settings');
            const data = await response.json();
            
            switchMaster.checked = data.is_active;
            elMasterStatus.innerText = data.is_active ? "Active" : "Paused";
            inputMonthly.value = data.monthly_limit;
            inputDaily.value = data.daily_limit;

            // Update Quota Bars
            const mPer = Math.min(100, (data.monthly_usage / data.monthly_limit) * 100);
            const dPer = Math.min(100, (data.daily_usage / data.daily_limit) * 100);
            
            elQuotaMonthlyText.innerText = `${formatNum(data.monthly_usage)} / ${formatNum(data.monthly_limit)}`;
            elQuotaDailyText.innerText   = `${formatNum(data.daily_usage)} / ${formatNum(data.daily_limit)}`;
            
            progressMonthly.style.width = `${mPer}%`;
            progressDaily.style.width = `${dPer}%`;

        } catch (error) {
            console.error("Failed to fetch settings:", error);
        }
    }

    async function saveSettings(payload) {
        try {
            const response = await fetch('/admin/settings', {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            await fetchSettings();
        } catch (error) {
            console.error("Failed to save settings:", error);
        }
    }

    btnSave.addEventListener('click', () => {
        saveSettings({
            monthly_limit: parseInt(inputMonthly.value),
            daily_limit: parseInt(inputDaily.value)
        });
    });

    switchMaster.addEventListener('change', () => {
        saveSettings({ is_active: switchMaster.checked });
    });

    // Tab Switching
    const tabBtns = document.querySelectorAll('.tab-btn');
    const viewPanels = document.querySelectorAll('.view-panel');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const target = btn.dataset.tab;
            
            tabBtns.forEach(b => b.classList.remove('active'));
            viewPanels.forEach(p => p.classList.remove('active'));
            
            btn.classList.add('active');
            document.getElementById(target).classList.add('active');
        });
    });

    // Intelligence Search
    const inputSearch = document.getElementById('input-search');
    const btnSearch   = document.getElementById('btn-search-trigger');
    const resultsArea = document.getElementById('search-results-container');

    async function performSearch() {
        const query = inputSearch.value.trim();
        if (!query) return;

        btnSearch.disabled = true;
        btnSearch.innerText = "Scanning...";
        resultsArea.innerHTML = `
            <div class="glass" style="padding:50px; text-align:center;">
                <div class="scan-pulse">⚡</div>
                <p style="margin-top:15px; color:var(--text-secondary);">Running deep database query...</p>
            </div>`;

        try {
            const response = await fetch(`/admin/search?q=${encodeURIComponent(query)}`);
            const data = await response.json();

            resultsArea.innerHTML = '';

            if (data.length === 0) {
                resultsArea.innerHTML = `
                    <div class="glass" style="padding:50px; text-align:center;">
                        <div style="font-size:40px; margin-bottom:15px;">🔍</div>
                        <h3>No Intelligence Found</h3>
                        <p style="color:var(--text-secondary); margin-top:8px;">
                            This domain hasn't been processed yet. The engine will discover it automatically.
                        </p>
                    </div>`;
                return;
            }

            data.forEach(item => {
                const card = document.createElement('div');
                card.className = 'result-card glass';

                // Pattern badges
                const patternsHtml = item.patterns.length
                    ? item.patterns.map(p => `<span class="pattern-badge">📧 ${p}</span>`).join(' ')
                    : '<span class="pattern-badge" style="opacity:0.5">No pattern detected yet</span>';

                // Confidence bar helper
                const confBar = (conf) => {
                    const pct = Math.round((conf ?? 0) * 100);
                    if (pct >= 90) return `<span style="color:#10b981; font-weight:700;">High Quality</span>`;
                    if (pct >= 60) return `<span style="color:#f59e0b; font-weight:700;">Verified</span>`;
                    return `<span style="color:#6b7280; font-weight:700;">Infered</span>`;
                };

                // Email rows
                const emailRowsHtml = item.emails.map(e => {
                    const highlight = e.is_queried
                        ? 'background: rgba(59,130,246,0.12); border-left: 3px solid var(--accent-blue);'
                        : '';
                    const tag = e.is_queried
                        ? '<span class="pattern-badge" style="background:rgba(59,130,246,0.15); color:var(--accent-blue); margin-left:8px;">Queried</span>'
                        : '';
                    const personTag = e.person
                        ? `<span class="email-person">👤 ${e.person}</span>`
                        : '';
                    const statusIcon = e.status === 'valid' ? '✅' : '⚠️';

                    return `
                        <tr style="${highlight}">
                            <td>
                                <span class="email-user">${e.email}</span>${tag}
                                ${personTag}
                            </td>
                            <td>${statusIcon} ${e.status}</td>
                            <td><span class="badge ${e.is_used ? 'usage-used' : 'usage-available'}">${e.is_used ? 'Used' : 'Available'}</span></td>
                        </tr>`;
                }).join('');

                card.innerHTML = `
                    <!-- Company Header -->
                    <div class="result-header">
                        <div class="result-domain-info">
                            <h3>🏢 ${item.domain}</h3>
                            <div style="margin-top:8px;">${patternsHtml}</div>
                        </div>
                        <div style="display:flex; gap:10px; flex-wrap:wrap; text-align:center;">
                            <div class="stat-pill">
                                <div class="stat-pill-value">${formatNum(item.total_emails)}</div>
                                <div class="stat-pill-label">Total Contacts</div>
                            </div>
                            <div class="stat-pill verified">
                                <div class="stat-pill-value">${formatNum(item.verified_count)}</div>
                                <div class="stat-pill-label">Verified</div>
                            </div>
                            <div class="stat-pill named">
                                <div class="stat-pill-value">${formatNum(item.named_count)}</div>
                                <div class="stat-pill-label">Named Staff</div>
                            </div>
                        </div>
                    </div>

                    <!-- Contacts Table -->
                    <div class="table-container" style="max-height:400px;">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>Contact</th>
                                    <th>Status</th>
                                    <th>Confidence</th>
                                    <th>Usage</th>
                                </tr>
                            </thead>
                            <tbody>${emailRowsHtml}</tbody>
                        </table>
                    </div>`;

                resultsArea.appendChild(card);
            });

        } catch (error) {
            console.error("Search failed:", error);
            resultsArea.innerHTML = `<div class="glass" style="padding:40px; text-align:center; color:#ef4444;">⚠️ SEARCH FAILED — Check console for details</div>`;
        } finally {
            btnSearch.disabled = false;
            btnSearch.innerText = "⚡ Deep Query";
        }
    }

    btnSearch.addEventListener('click', performSearch);
    inputSearch.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') performSearch();
    });

    async function fetchStats() {
        try {
            const response = await fetch('/stats');
            const data = await response.json();
            
            elDomains.innerText      = formatNum(data.domains);
            elCompleted.innerText    = formatNum(data.completed_domains);
            elValidMails.innerText   = formatNum(data.available_emails);
            elPatternMails.innerText = formatNum(data.pattern_emails);
        } catch (error) {
            console.error("Failed to fetch stats:", error);
        }
    }

    async function fetchEmails() {
        try {
            const response = await fetch('/emails');
            const data = await response.json();
            
            if (data.length === 0) return;

            const displayData = data.slice(-100).reverse();

            elTableBody.innerHTML = '';

            displayData.forEach(item => {
                const tr = document.createElement('tr');
                
                const sourceBadge = item.source === 'scraper' 
                    ? '<span class="badge source-scraper">Scraped</span>' 
                    : '<span class="badge source-pattern">Inferred</span>';
                
                const statusBadge = item.status === 'valid'
                    ? '<span class="badge status-valid">✓ Valid</span>'
                    : '<span class="badge status-invalid">✗ Fail</span>';

                const usageBadge = item.is_used 
                    ? '<span class="badge usage-used">Used</span>'
                    : '<span class="badge usage-available">Available</span>';

                tr.innerHTML = `
                    <td style="font-weight:500;">${item.email}</td>
                    <td style="color:var(--text-secondary);">${item.domain}</td>
                    <td>${statusBadge}</td>
                    <td>${usageBadge}</td>`;
                elTableBody.appendChild(tr);
            });

        } catch (error) {
            console.error("Failed to fetch emails:", error);
        }
    }

    btnExport.addEventListener('click', () => {
        window.location.href = '/emails/export';
    });

    fetchStats();
    fetchEmails();
    fetchSettings();
    setInterval(fetchStats, 5000);
    setInterval(fetchEmails, 10000);
    setInterval(fetchSettings, 30000);
});
