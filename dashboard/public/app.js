/**
 * Mesh Control Plane — Real-Time Web Dashboard Portal
 * Dynamic DOM Renderer & Network Topology Visualizer
 *
 * Architecture:
 *   • 7 Physical Wireless Radios (NetMetal AX): Form an explicit 7-Sided Polygon (Heptagon)
 *   • GCS Radio (7th vertex of polygon) connects via Ethernet Switch to GCS-01, GCS-02, GCS-03 (OUTSIDE polygon)
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
        led.className = 'status-indicator degraded';
        title.textContent = 'SYSTEM DEGRADED';
        title.style.color = 'var(--accent-amber)';
        sub.textContent = `${summary.online_nodes} / ${summary.total_nodes} Devices Active`;
    }
}

// Render SVG 7-Sided Polygon (Heptagon) Wireless Topology Graph
function renderTopology(topology) {
    if (!topology || !topology.nodes) return;
    const svg = document.getElementById('topology-svg');

    // 7 Vertices of the 7-Sided Polygon (6 UGV NetMetal AX Radios + 1 GCS Radio)
    const radioOrder = [
        'UGV-01', 'UGV-02', 'UGV-03', 'UGV-04', 'UGV-05', 'UGV-06', 'GCS-RADIO'
    ];

    const positions = {};
    const cx = 270;
    const cy = 170;
    const rx = 190;
    const ry = 110;
    const n = radioOrder.length; // 7

    const polygonPoints = [];
    for (let i = 0; i < n; i++) {
        // Position GCS-RADIO explicitly at angle 0 (rightmost vertex of polygon)
        const angle = (2 * Math.PI * i / n);
        const ptX = Math.round(cx + rx * Math.cos(angle));
        const ptY = Math.round(cy + ry * Math.sin(angle));
        positions[radioOrder[i]] = { x: ptX, y: ptY };
        polygonPoints.push(`${ptX},${ptY}`);
    }

    // Connect Ethernet Switch and 3 GCS Stations directly to GCS-RADIO
    const gcsRadioPos = positions['GCS-RADIO']; // GCS-RADIO point (rightmost vertex)
    const switchX = gcsRadioPos.x + 75; // x = ~535
    positions['GCS-01'] = { x: gcsRadioPos.x + 180, y: 65 };
    positions['GCS-02'] = { x: gcsRadioPos.x + 180, y: 170 };
    positions['GCS-03'] = { x: gcsRadioPos.x + 180, y: 275 };

    let html = '';

    // 1. Explicit 7-Sided Polygon (Heptagon) Perimeter Outline
    html += `
        <!-- 7-Sided Polygon Perimeter -->
        <polygon points="${polygonPoints.join(' ')}" 
                 fill="rgba(0, 229, 255, 0.03)" 
                 stroke="rgba(0, 229, 255, 0.4)" 
                 stroke-width="2" 
                 stroke-dasharray="6 3" />
        <text x="${cx}" y="24" fill="var(--accent-cyan)" font-size="11" font-weight="700" text-anchor="middle">
            7-SIDED POLYGON WIRELESS MESH (7 NETMETAL AX RADIOS)
        </text>
    `;

    // Create lookup for online status
    const nodeStatusMap = {};
    topology.nodes.forEach(node => {
        nodeStatusMap[node.id] = node.status;
    });

    const gcsAnyOnline = nodeStatusMap['GCS-01'] === 'ONLINE' || 
                         nodeStatusMap['GCS-02'] === 'ONLINE' || 
                         nodeStatusMap['GCS-03'] === 'ONLINE';
    nodeStatusMap['GCS-RADIO'] = gcsAnyOnline ? 'ONLINE' : 'OFFLINE';

    // 2. Draw 7-Sided Polygon Wireless Mesh Interconnection Lines
    topology.links.forEach(link => {
        const src = positions[link.source];
        const tgt = positions[link.target];
        if (!src || !tgt) return;

        // Skip mesh links to offline radio endpoints
        if (nodeStatusMap[link.source] !== 'ONLINE' || nodeStatusMap[link.target] !== 'ONLINE') {
            return;
        }

        let strokeColor = '#10b981'; // Green
        if (link.quality === 'GOOD') strokeColor = '#f59e0b';
        if (link.quality === 'POOR') strokeColor = '#f43f5e';

        html += `
            <line x1="${src.x}" y1="${src.y}" x2="${tgt.x}" y2="${tgt.y}" 
                  stroke="${strokeColor}" stroke-width="1.8" stroke-dasharray="4 2" opacity="0.65" />
        `;
    });

    // 3. Draw Ethernet Switch Hub & Connection Lines DIRECTLY FROM GCS-RADIO TO GCS STATIONS
    html += `
        <!-- Ethernet Switch Icon/Box -->
        <rect x="${switchX - 22}" y="152" width="44" height="36" rx="4" 
              fill="rgba(168, 85, 247, 0.2)" stroke="#a855f7" stroke-width="1.5" />
        <text x="${switchX}" y="174" fill="#a855f7" font-size="9" font-weight="800" text-anchor="middle">SWITCH</text>
        
        <!-- Connection from GCS-RADIO to Ethernet Switch -->
        <line x1="${gcsRadioPos.x}" y1="${gcsRadioPos.y}" x2="${switchX - 22}" y2="170" 
              stroke="#a855f7" stroke-width="2" stroke-dasharray="2 2" />
    `;

    // Connect Ethernet Switch to 3 GCS Stations
    ['GCS-01', 'GCS-02', 'GCS-03'].forEach(gcsId => {
        const tgt = positions[gcsId];
        const isOnline = nodeStatusMap[gcsId] === 'ONLINE';
        const color = isOnline ? '#a855f7' : 'rgba(244, 63, 94, 0.4)';

        html += `
            <line x1="${switchX + 22}" y1="170" x2="${tgt.x - 28}" y2="${tgt.y}" 
                  stroke="${color}" stroke-width="2" opacity="${isOnline ? 0.9 : 0.4}" />
        `;
    });

    // 4. Draw 7-Sided Polygon Corner Nodes (UGV-01..06 + GCS Radio)
    radioOrder.forEach(rId => {
        const pos = positions[rId];
        const isOnline = nodeStatusMap[rId] === 'ONLINE';
        const isGCSRadio = rId === 'GCS-RADIO';
        const color = !isOnline ? '#f43f5e' : (isGCSRadio ? '#a855f7' : '#00e5ff');
        const label = isGCSRadio ? 'GCS Radio' : rId;

        html += `
            <g transform="translate(${pos.x}, ${pos.y})" opacity="${isOnline ? 1.0 : 0.45}">
                <polygon points="0,-18 16,-8 16,12 0,20 -16,12 -16,-8" fill="rgba(15, 23, 42, 0.95)" stroke="${color}" stroke-width="2.5" />
                <circle r="4" fill="${color}" />
                <text y="32" fill="#f1f5f9" font-size="10" font-weight="700" text-anchor="middle">${label}</text>
            </g>
        `;
    });

    // 5. Draw 3 GCS Processing Stations connected to GCS Radio via Ethernet Switch (OUTSIDE polygon)
    ['GCS-01', 'GCS-02', 'GCS-03'].forEach(gcsId => {
        const pos = positions[gcsId];
        const isOnline = nodeStatusMap[gcsId] === 'ONLINE';
        const color = isOnline ? '#a855f7' : '#f43f5e';
        const statusText = isOnline ? '192.168.3.' + (gcsId === 'GCS-01' ? '71' : (gcsId === 'GCS-02' ? '72' : '73')) : 'OFFLINE';

        html += `
            <g transform="translate(${pos.x}, ${pos.y})" opacity="${isOnline ? 1.0 : 0.45}">
                <rect x="-28" y="-14" width="56" height="28" rx="6" fill="rgba(15, 23, 42, 0.95)" stroke="${color}" stroke-width="2" />
                <text y="4" fill="#f1f5f9" font-size="10" font-weight="700" text-anchor="middle">${gcsId}</text>
                <text y="24" fill="${isOnline ? '#94a3b8' : '#f43f5e'}" font-size="9" text-anchor="middle">${statusText}</text>
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
        if (activeFilter === 'offline') return node.status === 'OFFLINE';
        return node.type === activeFilter;
    });

    filtered.forEach(dev => {
        const isUGV = dev.type === 'UGV';
        const isOnline = dev.status === 'ONLINE';
        const typeClass = isUGV ? 'ugv' : 'gcs';
        const cardClass = isOnline ? 'device-card' : 'device-card offline';

        const statusBadge = isOnline 
            ? `<span class="dev-status-badge online">ONLINE</span>`
            : `<span class="dev-status-badge offline">OFFLINE</span>`;

        const signalVal = isOnline ? `${dev.rssi} dBm` : 'N/A';
        const latencyVal = isOnline ? `${dev.latency} ms` : 'Disconnected';

        html += `
            <div class="${cardClass}">
                <div class="device-header">
                    <span class="device-id">${dev.id}</span>
                    <div style="display: flex; gap: 6px; align-items: center;">
                        ${statusBadge}
                        <span class="device-type ${typeClass}">${dev.type}</span>
                    </div>
                </div>
                
                <div class="device-info">
                    <strong>${dev.name}</strong>
                    <span>IP: ${dev.ip}</span>
                    <span>Role: ${dev.role}</span>
                    <span>H/W: ${dev.hardware}</span>
                </div>

                <div class="device-metrics">
                    <div class="metric-item">
                        <span class="metric-val ${isOnline ? 'text-emerald' : 'text-dim'}">${signalVal}</span>
                        <span>Signal (RSSI)</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-val ${isOnline ? 'text-cyan' : 'text-dim'}">${latencyVal}</span>
                        <span>Latency</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-val ${isOnline ? 'text-amber' : 'text-dim'}">${dev.loss.toFixed(1)} %</span>
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
