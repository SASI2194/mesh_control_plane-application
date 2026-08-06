/**
 * Mesh Control Plane — Real-Time Web Dashboard Portal
 * Dynamic DOM Renderer & Network Topology Visualizer
 *
 * Architecture:
 *   • 7 Physical Wireless Radios (NetMetal AX): Form an explicit 7-Sided Polygon (Heptagon)
 *   • UGV-01 moved UP to top-right vertex
 *   • GCS Radio moved DOWN to center-right vertex (rightmost tip)
 *   • Ethernet Switch moved ASIDE to the right of GCS Radio, clear of all nodes
 *   • Real-Time Topic Table displays Live Rate (Hz), Msg Size (KB/MB), and Live Bandwidth
 *   • Ultra-Fast Live Polling: 500 ms (2 Hz live stream updates)
 */

let activeFilter = 'all';
let cachedData = null;

// Initialize Dashboard
document.addEventListener('DOMContentLoaded', () => {
    setupFilterListeners();
    fetchTelemetryData();
    setInterval(fetchTelemetryData, 500); // Poll every 500ms (2 Hz live updates)
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

    // Local Device Identity Header Info
    const localInfo = document.getElementById('local-device-info');
    if (localInfo && summary.local_node_id) {
        localInfo.textContent = `${summary.local_node_id} • ${summary.local_node_ip}`;
    }

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

    // Order vertices around Heptagon: UGV-01 UP, GCS-RADIO DOWN to center-right tip
    const radioOrder = [
        'UGV-06',      // Vertex 0: Top Center (-90°)
        'UGV-01',      // Vertex 1: Top Right (-38.5°)  [MOVED UP]
        'GCS-RADIO',   // Vertex 2: Center Right (+12.8°) [MOVED DOWN to rightmost tip]
        'UGV-02',      // Vertex 3: Bottom Right (+64.3°)
        'UGV-03',      // Vertex 4: Bottom Left (+115.7°)
        'UGV-04',      // Vertex 5: Center Left (+167.1°)
        'UGV-05'       // Vertex 6: Top Left (+218.5°)
    ];

    const positions = {};
    const cx = 260;
    const cy = 175;
    const rx = 195;
    const ry = 110;
    const n = radioOrder.length; // 7

    const polygonPoints = [];
    for (let i = 0; i < n; i++) {
        const angle = (2 * Math.PI * i / n) - (Math.PI / 2);
        const ptX = Math.round(cx + rx * Math.cos(angle));
        const ptY = Math.round(cy + ry * Math.sin(angle));
        positions[radioOrder[i]] = { x: ptX, y: ptY };
        polygonPoints.push(`${ptX},${ptY}`);
    }

    // Connect Ethernet Switch & 3 GCS Stations to GCS-RADIO (moved aside to the right)
    const gcsRadioPos = positions['GCS-RADIO']; // x = ~455, y = ~195
    const switchX = gcsRadioPos.x + 95;        // x = ~550 (moved ASIDE, clear of all nodes)
    const switchY = gcsRadioPos.y;

    positions['GCS-01'] = { x: switchX + 115, y: 65 };
    positions['GCS-02'] = { x: switchX + 115, y: 175 };
    positions['GCS-03'] = { x: switchX + 115, y: 285 };

    let html = '';

    // 1. Explicit 7-Sided Polygon (Heptagon) Perimeter Outline
    html += `
        <!-- 7-Sided Polygon Perimeter -->
        <polygon points="${polygonPoints.join(' ')}" 
                 fill="rgba(0, 229, 255, 0.03)" 
                 stroke="rgba(0, 229, 255, 0.4)" 
                 stroke-width="2" 
                 stroke-dasharray="6 3" />
        <text x="${cx}" y="22" fill="var(--accent-cyan)" font-size="11" font-weight="700" text-anchor="middle">
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

    // 3. Draw Ethernet Switch Hub (MOVED ASIDE) & Connection Lines DIRECTLY FROM GCS-RADIO TO GCS STATIONS
    html += `
        <!-- Ethernet Switch Icon/Box -->
        <rect x="${switchX - 24}" y="${switchY - 18}" width="48" height="36" rx="6" 
              fill="rgba(168, 85, 247, 0.25)" stroke="#a855f7" stroke-width="1.8" />
        <text x="${switchX}" y="${switchY + 4}" fill="#a855f7" font-size="9" font-weight="800" text-anchor="middle">SWITCH</text>
        
        <!-- Connection line from GCS-RADIO to Ethernet Switch -->
        <line x1="${gcsRadioPos.x}" y1="${gcsRadioPos.y}" x2="${switchX - 24}" y2="${switchY}" 
              stroke="#a855f7" stroke-width="2" stroke-dasharray="3 2" />
    `;

    // Connect Ethernet Switch to 3 GCS Stations
    ['GCS-01', 'GCS-02', 'GCS-03'].forEach(gcsId => {
        const tgt = positions[gcsId];
        const isOnline = nodeStatusMap[gcsId] === 'ONLINE';
        const color = isOnline ? '#a855f7' : 'rgba(244, 63, 94, 0.4)';

        html += `
            <line x1="${switchX + 24}" y1="${switchY}" x2="${tgt.x - 28}" y2="${tgt.y}" 
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

// Render Priority Topics Table with Real-Time Hz, Msg Size, and Live Bandwidth
function renderTopics(topics) {
    if (!topics) return;
    const tbody = document.getElementById('topics-tbody');
    let html = '';

    topics.forEach(t => {
        const isAllowed = t.status === 'ALLOWED';
        const isShedded = t.status === 'SHEDDED';
        let statusClass = 'allowed';
        if (isShedded) statusClass = 'shedded';
        else if (!isAllowed) statusClass = 'blocked';

        let verifClass = 'text-emerald';
        if (t.verification === 'UNINITIATED') {
            verifClass = 'text-dim';
        } else if (t.verification === 'CAPACITY EXCEEDED') {
            verifClass = 'text-amber';
        } else if (t.verification && (t.verification.includes('LOSS') || t.verification.includes('SHEDDED'))) {
            verifClass = 'text-rose';
        }

        // Role badge styling
        const role = t.role || 'IDLE';
        let roleBadge = `<span class="role-badge idle">IDLE</span>`;
        if (role === 'PUBLISHER') roleBadge = `<span class="role-badge publisher">Tx PUBLISHER</span>`;
        else if (role === 'SUBSCRIBER') roleBadge = `<span class="role-badge subscriber">Rx SUBSCRIBER</span>`;
        else if (role === 'BOTH') roleBadge = `<span class="role-badge both">Tx/Rx DUAL</span>`;

        // Tx (Publisher) metrics
        const txHz = t.tx_hz !== undefined ? t.tx_hz.toFixed(1) : '0.0';
        const txMbps = t.tx_mbps !== undefined ? t.tx_mbps.toFixed(1) : '0.0';
        const txSize = t.tx_data_size_str || '0 B';
        const txStr = isAllowed && t.tx_hz > 0 ? `${txHz} Hz • ${txMbps} Mbps <br/><small class="text-dim">${txSize}</small>` : '<span class="text-dim">0.0 Hz • 0.0 Mbps</span>';

        // Rx (Subscriber) metrics
        const rxHz = t.rx_hz !== undefined ? t.rx_hz.toFixed(1) : '0.0';
        const rxMbps = t.rx_mbps !== undefined ? t.rx_mbps.toFixed(1) : '0.0';
        const rxSize = t.rx_data_size_str || '0 B';
        const rxStr = isAllowed && t.rx_hz > 0 ? `${rxHz} Hz • ${rxMbps} Mbps <br/><small class="text-dim">${rxSize}</small>` : '<span class="text-dim">0.0 Hz • 0.0 Mbps</span>';

        // Throughput Differential
        const diffMbps = t.diff_mbps !== undefined ? t.diff_mbps.toFixed(1) : '0.0';
        const delPct = t.delivery_pct !== undefined ? t.delivery_pct.toFixed(1) : '100.0';
        const diffColor = Math.abs(t.diff_mbps || 0) < 1.0 ? 'text-emerald' : 'text-amber';
        const diffStr = isAllowed ? `<span class="${diffColor} font-bold">${diffMbps} Mbps Δ</span> <br/><small class="text-cyan">${delPct}% Recv</small>` : '<span class="text-dim">0.0 Mbps Δ</span>';

        html += `
            <tr>
                <td><strong>P${t.priority}</strong></td>
                <td>${t.name}</td>
                <td>Priority ${t.priority}</td>
                <td>${roleBadge}</td>
                <td><span class="text-cyan font-bold">${txStr}</span></td>
                <td><span class="text-purple font-bold">${rxStr}</span></td>
                <td>${diffStr}</td>
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
        const isLocal = dev.is_local;
        const typeClass = isUGV ? 'ugv' : 'gcs';
        let cardClass = isOnline ? 'device-card' : 'device-card offline';
        if (isLocal) cardClass += ' local-host-card';

        const statusBadge = isOnline 
            ? `<span class="dev-status-badge online">ONLINE</span>`
            : `<span class="dev-status-badge offline">OFFLINE</span>`;

        const localBadge = isLocal 
            ? `<span class="dev-status-badge local-host">THIS DEVICE</span>`
            : '';

        const signalVal = isOnline ? `${dev.rssi} dBm` : 'N/A';
        const latencyVal = isOnline ? `${dev.latency} ms` : 'Disconnected';

        html += `
            <div class="${cardClass}">
                <div class="device-header">
                    <span class="device-id">${dev.id}</span>
                    <div style="display: flex; gap: 6px; align-items: center;">
                        ${localBadge}
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
