document.addEventListener('DOMContentLoaded', () => {
    
    // Elements
    const elAvailable   = document.getElementById('stat-available');
    const elUsed        = document.getElementById('stat-used');
    const elTime        = document.getElementById('sys-time');
    const elUptime      = document.getElementById('sys-uptime');
    const elResults     = document.getElementById('results-list');
    const elLiveLogs    = document.getElementById('live-logs');
    const btnGenerate   = document.getElementById('btn-generate');
    const btnExport     = document.getElementById('btn-export');
    const elProgress    = document.getElementById('gen-progress');

    let startTime = Date.now();

    // Utility: format numbers with commas
    const formatNum = (num) => new Intl.NumberFormat('en-US').format(num ?? 0);

    // Update Clock & Uptime
    function updateClock() {
        const now = new Date();
        elTime.innerText = now.toLocaleTimeString('en-GB');
        
        const seconds = Math.floor((Date.now() - startTime) / 1000);
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        elUptime.innerText = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }

    // Add Live Log
    function addLog(msg) {
        const div = document.createElement('div');
        div.className = 'log-item fade-in';
        div.innerHTML = `<span>[${new Date().toLocaleTimeString('en-GB')}]</span> ${msg}`;
        elLiveLogs.prepend(div);
        
        if (elLiveLogs.children.length > 50) {
            elLiveLogs.removeChild(elLiveLogs.lastChild);
        }
    }

    // Fetch Stats
    async function fetchStats() {
        try {
            const response = await fetch('/stats');
            const data = await response.json();
            
            elAvailable.innerText = formatNum(data.available_emails);
            elUsed.innerText      = formatNum(data.used_emails);
        } catch (error) {
            console.error("Failed to fetch stats:", error);
        }
    }

    // Export Logic
    async function handleExport() {
        addLog("INITIATING INTELLIGENCE EXPORT...");
        window.location.href = '/emails/export';
    }

    // Generation Handler
    async function generateData() {
        btnGenerate.disabled = true;
        elProgress.style.display = 'block';
        
        try {
            addLog("REQUESTING NEW INTELLIGENCE BATCH...");
            const response = await fetch('/emails/generate', { method: 'POST' });
            const data = await response.json();

            if (data.length === 0) {
                addLog("FAILED: NO AVAILABLE DATA IN QUEUE");
                alert("No new data available to generate.");
            } else {
                addLog(`BATCH SECURED: ${data.length} RECORDS RECEIVED`);
                
                // Clear empty state if first run
                if (elResults.querySelector('.empty-state')) {
                    elResults.innerHTML = '';
                }

                data.forEach((item, index) => {
                    setTimeout(() => {
                        const row = document.createElement('div');
                        row.className = 'data-row fade-in';
                        row.innerHTML = `
                            <div class="email">${item.email}</div>
                            <div class="domain">${item.domain}</div>
                            <div class="tag">${item.confidence > 0.8 ? 'HIGH_CONF' : 'VERIFIED'}</div>
                            <div class="action">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="cursor:pointer; opacity:0.5;" onclick="navigator.clipboard.writeText('${item.email}')">
                                    <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path>
                                    <rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect>
                                </svg>
                            </div>
                        `;
                        elResults.prepend(row);
                        
                        if (index === data.length - 1) {
                            addLog("DUMP COMPLETE. DATA PERSISTED.");
                            fetchStats();
                        }
                    }, index * 20); // Faster staggered entry
                });
            }
        } catch (error) {
            addLog(`CRITICAL SYSTEM ERROR: ${error.message}`);
        } finally {
            btnGenerate.disabled = false;
            elProgress.style.display = 'none';
        }
    }

    // Listeners
    btnGenerate.addEventListener('click', generateData);
    btnExport.addEventListener('click', handleExport);

    // Mobile Menu Toggle
    const btnMenu = document.getElementById('menu-toggle');
    const elSidebar = document.querySelector('.sidebar');
    
    if (btnMenu) {
        btnMenu.addEventListener('click', (e) => {
            e.stopPropagation();
            elSidebar.classList.toggle('active');
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            if (elSidebar.classList.contains('active') && !elSidebar.contains(e.target)) {
                elSidebar.classList.remove('active');
            }
        });
    }

    // Boot & Loop
    fetchStats();
    setInterval(fetchStats, 10000);
    setInterval(updateClock, 1000);
    
    addLog("INTELLIGENCE_ENGINE_V2 CORE INITIALIZED");
});
