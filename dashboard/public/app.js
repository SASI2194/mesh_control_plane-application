/**
 * Mesh Control Plane — Real-Time Web Dashboard Portal
 * Dynamic DOM Renderer & Network Topology Visualizer
 */

let activeFilter = 'all';
let cachedData = null;

// Initialize Dashboard
document.addEventListener('DOMContentLoaded', () => {
    setupFilterListeners();
    fetchTelemetryData();
    setInterval(fetchTelemetryData, 1500); // Poll every 1.5 seconds
});

// Setup Filter Buttons
function setupFilterListeners() {
    const buttons = document.querySelectorAll('.filter-pills .pill');
    buttons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            buttons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            activeFilter = btn.getAttribute('data-filter');
            if (cachedData) {
                renderDeviceCards(cachedData.nodes);
            }
        });
    });
}

// Fetch Data from Telemetry REST Endpoint
async function fetchTelemetryData() {
    try {
        const response = await fetch('/api/all');
        if (!response.ok) return;
        const data = await response.json();
        cachedData = data;

        renderSummary(data.summary);
        renderTopology(data.topology);
        renderTopics(data.topics);
        renderDeviceCards(data.nodes);
    } catch (err) {
        console.warn('Telemetry fetch error:', err);
    }
}

// Render Header Summary & KPI Cards
function renderSummary(summary) {
    if (!summary) return;

    // KPI Values
    document.getElementById('kpi-active-nodes').textContent = `${summary.online_nodes} / ${summary.total_nodes}`;
    document.getElementById('kpi-bandwidth').textContent = `${summary.used_bandwidth_mbps.toFixed(0)} / ${summary.max_bandwidth_mbps.toFixed(0)} Mbps`;
    document.getElementById('kpi-loss-limit').textContent = `${summary.loss_tolerance_percent.toFixed(1)} %`;

    // Progress bar fill
    const pct = Math.min(100, (summary.used_bandwidth_mbps / summary.max_bandwidth_mbps) * 100);
    document.getElementById('kpi-bw-progress').style.width = `${pct}%`;

    // Status Badge
    const led = document.getElementById('global-status-led');
    const title = document.getElementById('global-status-title');
    const sub = document.getElementById('global-status-sub');

    if (summary.system_health === 'OPTIMAL') {
        led.className = 'status-indicator online';
        title.textContent = 'SYSTEM OPTIMAL';
        title.style.color = 'var(--accent-emerald)';
        sub.textContent = `${summary.online_nodes} / ${summary.total_nodes} Devices Active`;
    } else {
        led.className = 'status-indicator offline';
        title.textContent = 'SYSTEM DEGRADED';
        title.style.color = 'var(--accent-amber)';
        sub.textContent = `${summary.online_nodes} / ${summary.total_nodes} Devices Active`;
    }
}

// Render SVG Mesh Topology Graph (6 UGVs + 3 GCSs)
function renderTopology(topology) {
    if (!topology || !topology.nodes) return;
    const svg = document.getElementById('topology-svg');

    // Layout node coordinates (3 GCSs on left, 6 UGVs in arc/grid on right)
    const positions = {
        'GCS-01': { x: 120, y: 80 },
        'GCS-02': { x: 120, y: 170 },
        'GCS-03': { x: 120, y: 260 },

        'UGV-01': { x: 380, y: 170 }, // Router / Mesh Hub UGV

        'UGV-02': { x: 620, y: 60 },
        'UGV-03': { x: 650, y: 130 },
        'UGV-04': { x: 650, y: 210 },
        'UGV-05': { x: 620, y: 280 },
        'UGV-06': { x: 480, y: 270 },
    };

    let html = '';

    // Draw Links
    topology.links.forEach(link => {
        const src = positions[link.source];
        const tgt = positions[link.target];
        if (!src || !tgt) return;

        let strokeColor = '#10b981'; // Green
        if (link.quality === 'GOOD') strokeColor = '#f59e0b'; // Yellow
        if (link.quality === 'POOR') strokeColor = '#f43f5e'; // Red

        html += `
            <line x1="${src.x}" y1="${src.y}" x2="${tgt.x}" y2="${tgt.y}" 
                  stroke="${strokeColor}" stroke-width="2" stroke-dasharray="4 2" opacity="0.85" />
            <text x="${(src.x + tgt.x)/2}" y="${(src.y + tgt.y)/2 - 5}" 
                  fill="#94a3b8" font-size="10" text-anchor="middle">${link.rssi} dBm</text>
        `;
    });

    // Draw Nodes
    topology.nodes.forEach(node => {
        const pos = positions[node.id];
        if (!pos) return;

        const isGCS = node.type === 'GCS';
        const color = isGCS ? '#a855f7' : '#00e5ff';
        const radius = node.id === 'UGV-01' || node.id === 'GCS-01' ? 22 : 18;

        html += `
            <g transform="translate(${pos.x}, ${pos.y})">
                <circle r="${radius}" fill="rgba(15, 23, 42, 0.9)" stroke="${color}" stroke-width="2.5" />
                <circle r="6" fill="${color}" />
                <text y="${radius + 14}" fill="#f1f5f9" font-size="11" font-weight="700" text-anchor="middle">${node.id}</text>
                <text y="${radius + 26}" fill="#94a3b8" font-size="9" text-anchor="middle">${node.ip}</text>
            </g>
        `;
    });

    svg.innerHTML = html;
}

// Render Priority Topics Table
function renderTopics(topics) {
    if (!topics) return;
    const tbody = document.getElementById('topics-tbody');
    let html = '';

    topics.forEach(t => {
        const isAllowed = t.status === 'ALLOWED';
        const statusClass = isAllowed ? 'allowed' : 'blocked';
        const verifClass = isAllowed ? 'text-emerald' : 'text-amber';

        html += `
            <tr>
                <td><strong>P${t.priority}</strong></td>
                <td>${t.name}</td>
                <td>Priority ${t.priority}</td>
                <td>${t.bandwidth_mbps} Mbps</td>
                <td><span class="status-badge ${statusClass}">${t.status}</span></td>
                <td class="${verifClass}">${t.verification}</td>
            </tr>
        `;
    });

    tbody.innerHTML = html;
}

// Render 9 Device Cards
function renderDeviceCards(nodes) {
    if (!nodes) return;
    const container = document.getElementById('device-cards-container');
    let html = '';

    const filtered = nodes.filter(node => {
        if (activeFilter === 'all') return true;
        return node.type === activeFilter;
    });

    filtered.forEach(dev => {
        const isUGV = dev.type === 'UGV';
        const typeClass = isUGV ? 'ugv' : 'gcs';

        html += `
            <div class="device-card">
                <div class="device-header">
                    <span class="device-id">${dev.id}</span>
                    <span class="device-type ${typeClass}">${dev.type}</span>
                </div>
                
                <div class="device-info">
                    <strong>${dev.name}</strong>
                    <span>IP: ${dev.ip}</span>
                    <span>Role: ${dev.role}</span>
                    <span>H/W: ${dev.hardware}</span>
                </div>

                <div class="device-metrics">
                    <div class="metric-item">
                        <span class="metric-val text-emerald">${dev.rssi} dBm</span>
                        <span>Signal (RSSI)</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-val text-cyan">${dev.latency} ms</span>
                        <span>Latency</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-val text-amber">${dev.loss.toFixed(1)} %</span>
                        <span>Packet Loss</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-val text-purple">${dev.uptime}</span>
                        <span>Uptime</span>
                    </div>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}
