document.addEventListener('DOMContentLoaded', () => {
    
    // Elements
    const elAvailable   = document.getElementById('stat-available');
    const elUsed        = document.getElementById('stat-used');
    const elTime        = document.getElementById('sys-time');
    const elUptime      = document.getElementById('sys-uptime');
    const elTerminal    = document.getElementById('terminal-out');
    const elLiveLogs    = document.getElementById('live-logs');
    const btnGenerate   = document.getElementById('btn-generate');
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
        div.className = 'log-item';
        div.innerText = `> ${msg}`;
        elLiveLogs.prepend(div);
        
        // Keep only last 20
        if (elLiveLogs.children.length > 20) {
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
            
            if (data.processing_domains > 0) {
                addLog(`CRUNCHING DOMAINS: ${data.processing_domains} ACTIVE`);
            }
        } catch (error) {
            console.error("Failed to fetch stats:", error);
        }
    }

    // Generation Handler
    async function generateData() {
        btnGenerate.disabled = true;
        elProgress.style.display = 'inline';
        elTerminal.innerHTML = "--------------------------------------------------\nINITIATING DATA DUMP...\n--------------------------------------------------\n";
        
        try {
            addLog("REQUESTING BATCH DATA...");
            const response = await fetch('/emails/generate', { method: 'POST' });
            const data = await response.json();

            if (data.length === 0) {
                elTerminal.innerHTML += "\n[ ERROR ]: NO FRESH DATA AVAILABLE IN SYSTEM INVENTORY.";
                addLog("GENERATION FAILED: NO DATA");
            } else {
                addLog(`BATCH SECURED: ${data.length} RECORDS`);
                
                // Typing Effect for results
                let i = 0;
                async function typeRow() {
                    if (i < data.length) {
                        const item = data[i];
                        const row = `[ DATA_RECORD ]: ${item.email.padEnd(30)} // SOURCE: ${item.source.toUpperCase().padEnd(10)} // DOMAIN: ${item.domain}\n`;
                        elTerminal.innerHTML += row;
                        elTerminal.scrollTop = elTerminal.scrollHeight;
                        i++;
                        
                        // Type first 50 fast, then batch balance for performance
                        if (i < 50) {
                            setTimeout(typeRow, 10);
                        } else if (i % 20 === 0) {
                            // Render in chunks of 20 to keep it feeling fast but "scrolling"
                            await new Promise(r => setTimeout(r, 10));
                            typeRow();
                        } else {
                            typeRow();
                        }
                    } else {
                        elTerminal.innerHTML += "\n--------------------------------------------------\n[ SUCCESS ]: DUMP COMPLETE. DATA MARKED AS USED.\n--------------------------------------------------";
                        addLog("BATCH GENERATION SUCCESSFUL");
                        fetchStats();
                    }
                }
                typeRow();
            }
        } catch (error) {
            elTerminal.innerHTML += `\n[ FATAL_ERROR ]: ${error.message}`;
            addLog(`CRITICAL ERROR: ${error.message}`);
        } finally {
            btnGenerate.disabled = false;
            elProgress.style.display = 'none';
        }
    }

    // Listeners
    btnGenerate.addEventListener('click', generateData);

    // Boot & Loop
    fetchStats();
    setInterval(fetchStats, 5000);
    setInterval(updateClock, 1000);
    
    addLog("V1.0 PROTOCOL INITIALIZED");
});
