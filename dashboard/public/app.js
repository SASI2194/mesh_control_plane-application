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
let neighborFilter = 'all';
let cachedData = null;

// Initialize Dashboard
document.addEventListener('DOMContentLoaded', () => {
    setupFilterListeners();
    setupNeighborFilterListeners();
    setupFleetModalListeners();
    setupNeighborModalListeners();
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

// Setup Table 2 Neighbor Filter Buttons
function setupNeighborFilterListeners() {
    const buttons = document.querySelectorAll('.neighbor-filter-pills .pill');
    buttons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            buttons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            neighborFilter = btn.getAttribute('data-neighbor-filter');
            if (cachedData) {
                renderNeighbourSelectionTable(cachedData.neighbor_table || cachedData.nodes);
            }
        });
    });
}

// Setup Neighbor Selection Formula Configuration Modal
function setupNeighborModalListeners() {
    const btnOpen = document.getElementById('btn-open-neighbor-config');
    const btnClose = document.getElementById('btn-close-neighbor-modal');
    const btnCancel = document.getElementById('btn-cancel-neighbor');
    const btnSave = document.getElementById('btn-save-neighbor');
    const modal = document.getElementById('neighbor-modal');

    const inW1 = document.getElementById('input-weight-rssi');
    const inW2 = document.getElementById('input-weight-lat');
    const inW3 = document.getElementById('input-weight-loss');
    const inW4 = document.getElementById('input-weight-snr');

    const inB1 = document.getElementById('input-bound-rssi');
    const inB2 = document.getElementById('input-bound-lat');
    const inB3 = document.getElementById('input-bound-loss');

    if (!btnOpen || !modal) return;

    btnOpen.addEventListener('click', async () => {
        modal.style.display = 'flex';
        try {
            const res = await fetch('/api/config/neighbor_selection');
            if (res.ok) {
                const data = await res.json();
                const weights = data.scoring_weights || {};
                const bounds = data.hard_boundaries || {};

                if (inW1) inW1.value = weights.rssi_weight !== undefined ? weights.rssi_weight : 0.40;
                if (inW2) inW2.value = weights.latency_weight !== undefined ? weights.latency_weight : 0.35;
                if (inW3) inW3.value = weights.packet_loss_weight !== undefined ? weights.packet_loss_weight : 0.15;
                if (inW4) inW4.value = weights.snr_weight !== undefined ? weights.snr_weight : 0.10;

                if (inB1) inB1.value = bounds.min_rssi_dbm !== undefined ? bounds.min_rssi_dbm : -85;
                if (inB2) inB2.value = bounds.max_latency_ms !== undefined ? bounds.max_latency_ms : 100;
                if (inB3) inB3.value = bounds.max_packet_loss_percent !== undefined ? bounds.max_packet_loss_percent : 10;
            }
        } catch (e) {
            console.error('Failed to load neighbor config:', e);
        }
    });

    const closeModal = () => { modal.style.display = 'none'; };
    if (btnClose) btnClose.addEventListener('click', closeModal);
    if (btnCancel) btnCancel.addEventListener('click', closeModal);

    if (btnSave) {
        btnSave.addEventListener('click', async () => {
            const payload = {
                scoring_weights: {
                    rssi_weight: parseFloat(inW1.value),
                    latency_weight: parseFloat(inW2.value),
                    packet_loss_weight: parseFloat(inW3.value),
                    snr_weight: parseFloat(inW4.value)
                },
                hard_boundaries: {
                    min_rssi_dbm: parseFloat(inB1.value),
                    max_latency_ms: parseFloat(inB2.value),
                    max_packet_loss_percent: parseFloat(inB3.value)
                }
            };

            try {
                const res = await fetch('/api/config/neighbor_selection', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                if (res.ok) {
                    alert('Neighbor Selection Formula Parameters Saved Successfully!');
                    closeModal();
                    fetchTelemetryData();
                }
            } catch (e) {
                alert('Failed to save neighbor config: ' + e);
            }
        });
    }
}

// Setup Fleet Device Count Configuration Modal
function setupFleetModalListeners() {
    const btnOpen = document.getElementById('btn-open-fleet-config');
    const btnClose = document.getElementById('btn-close-fleet-modal');
    const btnCancel = document.getElementById('btn-cancel-fleet');
    const btnSave = document.getElementById('btn-save-fleet');
    const modal = document.getElementById('fleet-modal');
    const selectCount = document.getElementById('fleet-count-select');
    const listContainer = document.getElementById('fleet-checkbox-list');

    if (!btnOpen || !modal) return;

    btnOpen.addEventListener('click', async () => {
        modal.style.display = 'flex';
        try {
            const res = await fetch('/api/config/fleet');
            if (res.ok) {
                const data = await res.json();
                selectCount.value = data.active_device_count || 9;
                listContainer.innerHTML = '';
                (data.devices || []).forEach(dev => {
                    const label = document.createElement('label');
                    label.style.display = 'flex';
                    label.style.alignItems = 'center';
                    label.style.gap = '6px';
                    label.style.fontSize = '12px';
                    label.style.color = '#cbd5e1';
                    label.style.cursor = 'pointer';
                    label.innerHTML = `<input type="checkbox" value="${dev.id}" ${dev.enabled ? 'checked' : ''} style="accent-color: #0284c7;"> <span style="font-weight: 600; color: ${dev.type === 'GCS' ? '#38bdf8' : '#e2e8f0'};">${dev.id}</span> (${dev.type})`;
                    listContainer.appendChild(label);
                });
            }
        } catch (e) {
            console.error('Failed to load fleet config:', e);
        }
    });

    const closeModal = () => { modal.style.display = 'none'; };
    btnClose.addEventListener('click', closeModal);
    btnCancel.addEventListener('click', closeModal);

    btnSave.addEventListener('click', async () => {
        const activeCount = parseInt(selectCount.value, 10);
        const checkedInputs = listContainer.querySelectorAll('input[type="checkbox"]:checked');
        const enabledDevices = Array.from(checkedInputs).map(i => i.value);

        try {
            const res = await fetch('/api/config/fleet', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    active_device_count: activeCount,
                    enabled_devices: enabledDevices
                })
            });
            if (res.ok) {
                alert(`Fleet Configuration Saved!\nActive Device Count: ${activeCount}\nEnabled Devices: ${enabledDevices.join(', ')}`);
                closeModal();
                fetchTelemetryData();
            }
        } catch (e) {
            alert('Failed to save fleet config: ' + e);
        }
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
        renderNetworkPeerTables(data.network_peer_tables || {});
        renderNetworkNeighborTable(data.network_neighbor_table || []);
        renderDeviceCards(data.nodes);
    } catch (err) {
        console.warn('Telemetry fetch error:', err);
    }
}

// Section 1: Render Network Peer Tables (Grouped per active node)
function renderNetworkPeerTables(peerTables) {
    const container = document.getElementById('network-peer-tables-container');
    if (!container || !peerTables) return;

    let html = '';
    const nodeKeys = Object.keys(peerTables);

    if (nodeKeys.length === 0) {
        container.innerHTML = `
            <div style="padding: 20px; text-align: center; color: #94a3b8; font-size: 13px;">
                No active network peers discovered on local NetMetal AX interfaces.
            </div>
        `;
        return;
    }

    nodeKeys.forEach(localId => {
        const rawData = peerTables[localId];
        let peers = [];
        let isLocal = false;
        let apRole = 'STATION_BRIDGE';
        let wifiStatus = '';

        if (Array.isArray(rawData)) {
            peers = rawData;
        } else if (rawData && typeof rawData === 'object') {
            peers = rawData.peers || [];
            isLocal = !!rawData.is_local;
            apRole = rawData.ap_role || 'STATION_BRIDGE';
            wifiStatus = rawData.wifi_status || '';
        }

        const countStr = `${peers.length} Discovered Peer${peers.length !== 1 ? 's' : ''}`;

        // Header Badges
        const localBadge = isLocal 
            ? `<span class="dev-status-badge local-host" style="font-size: 9px; padding: 2px 7px;">📍 THIS DEVICE</span>` 
            : '';

        let roleBadge = `<span class="dev-status-badge" style="background: rgba(14,165,233,0.15); color: #38bdf8; border: 1px solid rgba(56,189,248,0.3); font-size: 9px; padding: 2px 7px;">🔗 STATION BRIDGE</span>`;
        if (apRole === 'MASTER_AP' || apRole === 'ELECTED_MASTER_AP') {
            roleBadge = `<span class="dev-status-badge" style="background: linear-gradient(135deg, rgba(245,158,11,0.3), rgba(217,119,6,0.5)); color: #fbbf24; border: 1px solid #f59e0b; font-weight: 800; font-size: 9px; padding: 2px 7px;">👑 MASTER AP</span>`;
        }

        let wifiBadge = '';
        if (wifiStatus && isLocal) {
            wifiBadge = `<span class="role-badge publisher" style="font-size: 8.5px; padding: 2px 6px;">${wifiStatus}</span>`;
        }

        let rowsHtml = '';
        if (peers.length === 0) {
            rowsHtml = `
                <tr>
                    <td colspan="9" style="text-align: center; color: #94a3b8; font-size: 12px; padding: 14px;">
                        No active peers discovered on radio interface.
                    </td>
                </tr>
            `;
        } else {
            rowsHtml = peers.map(p => {
                const rssi = p.rssi;
                let rssiColor = '#f43f5e';
                if (rssi > -65) rssiColor = '#34d399';
                else if (rssi > -75) rssiColor = '#fbbf24';

                return `
                    <tr>
                        <td><strong style="color:#f8fafc;">${p.id}</strong></td>
                        <td><code style="color:#a855f7;">${p.mac}</code></td>
                        <td><code style="color:#38bdf8;">${p.ip}</code> <span style="font-size:10px; color:#94a3b8;">(${p.radio_ip ? p.radio_ip : p.ip})</span></td>
                        <td><span style="color:${rssiColor}; font-weight:700;">${rssi} dBm</span></td>
                        <td><span style="color:#cbd5e1;">${p.latency.toFixed(1)} ms</span></td>
                        <td><span style="color:${p.loss > 5 ? '#f43f5e' : '#cbd5e1'};">${p.loss.toFixed(1)}%</span></td>
                        <td><span style="color:#cbd5e1;">${p.snr} dB</span></td>
                        <td><strong style="color:#c084fc;">${p.score.toFixed(4)}</strong></td>
                        <td><span class="role-badge publisher" style="font-size:9.5px;">${p.rank}</span></td>
                    </tr>
                `;
            }).join('');
        }

        html += `
            <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(0, 229, 255, 0.2); border-radius: 8px; padding: 12px; margin-bottom: 4px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; flex-wrap: wrap; gap: 8px;">
                    <h3 style="font-size: 13px; font-weight: 700; color: #00e5ff; margin: 0; display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                        <span>📻</span> <strong>${localId} Discovered Peer Table</strong>
                        ${localBadge}
                        ${roleBadge}
                        ${wifiBadge}
                        <small style="color: #94a3b8; font-weight: 500;">(${countStr})</small>
                    </h3>
                    <span class="badge badge-cyan" style="font-size: 10px;">${localId} Radio Link Discovery</span>
                </div>
                <div class="table-responsive">
                    <table class="data-table" style="font-size: 11.5px;">
                        <thead>
                            <tr>
                                <th>Peer Node ID</th>
                                <th>MAC Address</th>
                                <th>IP Address</th>
                                <th>RSSI</th>
                                <th>Latency</th>
                                <th>Packet Loss</th>
                                <th>SNR</th>
                                <th>Link Score</th>
                                <th>Raw Link Quality Rank</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${rowsHtml}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}


// Section 3: Render Network-Wide Neighbour Selection Governance Table
function renderNetworkNeighborTable(neighbors) {
    const tbody = document.getElementById('network-neighbor-tbody');
    if (!tbody || !neighbors) return;

    tbody.innerHTML = '';

    neighbors.forEach(item => {
        const tr = document.createElement('tr');

        const localHtml = `<strong style="color: #38bdf8; font-size:13px;">${item.local_node}</strong>`;
        const peerHtml = `<strong style="color: #f8fafc; font-size:13px;">${item.peer_node}</strong>`;
        const scoreHtml = `<strong style="color: #c084fc; font-size:12.5px;">${item.score.toFixed(4)}</strong>`;
        const rankHtml = `<span style="font-size:11.5px; color:#cbd5e1; font-weight:600;">${item.raw_rank}</span>`;
        const prioHtml = `<span style="font-size:11.5px; color:#94a3b8;">${item.inclusivity_priority}</span>`;

        const role = item.assigned_role;
        let roleBadge = '';
        if (role === 'PRIMARY_ACTIVE' || role === 'ACTIVE_PRIMARY') {
            roleBadge = `<span class="badge" style="background: rgba(16,185,129,0.2); color: #34d399; border: 1px solid rgba(16,185,129,0.4); font-weight: 700;">⭐ PRIMARY ACTIVE</span>`;
        } else if (role === 'STANDBY_BACKUP' || role === 'ACTIVE_SECONDARY') {
            roleBadge = `<span class="badge" style="background: rgba(6,182,212,0.2); color: #22d3ee; border: 1px solid rgba(6,182,212,0.4); font-weight: 700;">🛡️ STANDBY BACKUP</span>`;
        } else {
            roleBadge = `<span class="badge" style="background: rgba(148,163,184,0.15); color: #94a3b8; border: 1px solid rgba(148,163,184,0.3);">💤 DISCOVERED IDLE</span>`;
        }

        let statusBadge = `<span class="status-pill online">ONLINE</span>`;

        tr.innerHTML = `
            <td>${localHtml}</td>
            <td>${peerHtml}</td>
            <td>${scoreHtml}</td>
            <td>${rankHtml}</td>
            <td>${prioHtml}</td>
            <td>${roleBadge}</td>
            <td>${statusBadge}</td>
        `;

        tbody.appendChild(tr);
    });
}

// Render Header Summary & KPI Cards
function renderSummary(summary) {
    if (!summary) return;

    const activeCount = summary.active_device_count || summary.total_nodes;
    const activeUgvs = summary.active_ugv_count !== undefined ? summary.active_ugv_count : 6;
    const activeGcss = summary.active_gcs_count !== undefined ? summary.active_gcs_count : 3;

    // KPI Values
    document.getElementById('kpi-active-nodes').textContent = `${summary.online_nodes} / ${activeCount}`;
    document.getElementById('kpi-bandwidth').textContent = `${summary.used_bandwidth_mbps.toFixed(0)} / ${summary.max_bandwidth_mbps.toFixed(0)} Mbps`;
    document.getElementById('kpi-loss-limit').textContent = `${summary.loss_tolerance_percent.toFixed(1)} %`;

    // Update Filter Pills dynamically
    const btnAll = document.querySelector('.filter-pills .pill[data-filter="all"]');
    const btnUGV = document.querySelector('.filter-pills .pill[data-filter="UGV"]');
    const btnGCS = document.querySelector('.filter-pills .pill[data-filter="GCS"]');
    if (btnAll) btnAll.textContent = `All Active (${activeCount})`;
    if (btnUGV) btnUGV.textContent = `UGVs (${activeUgvs})`;
    if (btnGCS) btnGCS.textContent = `GCSs (${activeGcss})`;

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
        sub.textContent = `${summary.online_nodes} / ${activeCount} Active Fleet Devices`;
    } else {
        led.className = 'status-indicator degraded';
        title.textContent = 'SYSTEM DEGRADED';
        title.style.color = 'var(--accent-amber)';
        sub.textContent = `${summary.online_nodes} / ${activeCount} Active Fleet Devices`;
    }

    // Master AP Failover Event Alert Banner
    let failoverBanner = document.getElementById('master-ap-failover-alert');
    if (summary.master_failover_event) {
        const ev = summary.master_failover_event;
        if (!failoverBanner) {
            failoverBanner = document.createElement('div');
            failoverBanner.id = 'master-ap-failover-alert';
            failoverBanner.style.cssText = 'background: linear-gradient(90deg, rgba(245,158,11,0.25), rgba(217,119,6,0.35)); border: 1px solid #f59e0b; border-radius: 8px; padding: 8px 16px; margin: 10px 0; color: #fbbf24; font-size: 11px; font-weight: 700; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 0 12px rgba(245,158,11,0.3);';
            const container = document.querySelector('.portal-container') || document.body;
            container.insertBefore(failoverBanner, container.firstChild);
        }
        failoverBanner.innerHTML = `
            <span>⚠️ <strong>AUTOMATIC MASTER AP FAILOVER ACTIVATED</strong>: ${ev.elected_node_id} (${ev.elected_node_ip}) elected as NEW MASTER AP!</span>
            <small style="color: #fde68a;">[Reason: ${ev.reason}]</small>
        `;
    } else if (failoverBanner) {
        failoverBanner.remove();
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
        const isDenied = t.status === 'DENIED';
        let statusClass = 'allowed';
        if (isShedded) statusClass = 'shedded';
        else if (isDenied) statusClass = 'blocked';
        else if (!isAllowed) statusClass = 'blocked';

        let verifClass = 'text-emerald';
        if (t.verification === 'UNINITIATED') {
            verifClass = 'text-dim';
        } else if (t.verification === 'CAPACITY EXCEEDED') {
            verifClass = 'text-amber';
        } else if (t.verification && (t.verification.includes('LOSS') || t.verification.includes('SHEDDED') || t.verification.includes('DENY'))) {
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

        const formattedId = typeof t.id === 'number' ? `T${String(t.id).padStart(2, '0')}` : (String(t.id).startsWith('T') ? String(t.id) : `T${String(t.id).padStart(2, '0')}`);

        html += `
            <tr>
                <td><strong>${formattedId}</strong></td>
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
        const isDisabled = dev.enabled === false || dev.status === 'DISABLED';
        const isLocal = dev.is_local;
        const typeClass = isUGV ? 'ugv' : 'gcs';
        let cardClass = isOnline ? 'device-card' : 'device-card offline';
        if (isDisabled) cardClass += ' disabled-card';
        if (isLocal) cardClass += ' local-host-card';

        const statusBadge = isDisabled
            ? `<span class="dev-status-badge" style="background: rgba(148,163,184,0.15); color: #94a3b8; border: 1px solid #475569; font-weight: 700;">FLEET DISABLED</span>`
            : (isOnline 
                ? `<span class="dev-status-badge online">ONLINE</span>`
                : `<span class="dev-status-badge offline">OFFLINE</span>`);

        const localBadge = isLocal 
            ? `<span class="dev-status-badge local-host">THIS DEVICE</span>`
            : '';

        let apBadge = `<span class="dev-status-badge" style="background: rgba(14,165,233,0.15); color: #38bdf8; border: 1px solid rgba(56,189,248,0.3);">🔗 STATION BRIDGE</span>`;
        if (isDisabled) {
            apBadge = `<span class="dev-status-badge" style="background: rgba(71,85,105,0.2); color: #64748b; border: 1px solid #334155;">⛔ INACTIVE</span>`;
        } else if (dev.is_master_ap) {
            apBadge = `<span class="dev-status-badge" style="background: linear-gradient(135deg, rgba(245,158,11,0.3), rgba(217,119,6,0.5)); color: #fbbf24; border: 1px solid #f59e0b; font-weight: 800;">👑 MASTER AP</span>`;
        } else if (dev.ap_role === 'UNKNOWN_AP_AVAILABLE') {
            apBadge = `<span class="dev-status-badge" style="background: rgba(0,229,255,0.15); color: #00e5ff; border: 1px solid rgba(0,229,255,0.4); font-weight: 700;">❓ UNKNOWN AP</span>`;
        } else if (dev.ap_role === 'SEARCH_PROBE') {
            apBadge = `<span class="dev-status-badge" style="background: rgba(168,85,247,0.15); color: #c084fc; border: 1px solid rgba(168,85,247,0.4); font-weight: 700;">🔍 PROBING</span>`;
        }

        let neighborBadge = '';
        if (isOnline && !isDisabled && !isLocal) {
            const nRole = dev.neighbor_role || 'DISCOVERED_IDLE';
            if (nRole === 'PRIMARY_ACTIVE') {
                neighborBadge = `<span class="dev-status-badge" style="background: rgba(16,185,129,0.2); color: #10b981; border: 1px solid #10b981; font-weight: 800;">⭐ PRIMARY NEIGHBOR</span>`;
            } else if (nRole === 'STANDBY_BACKUP') {
                neighborBadge = `<span class="dev-status-badge" style="background: rgba(2,132,199,0.2); color: #38bdf8; border: 1px solid #0284c7; font-weight: 800;">🛡️ STANDBY BACKUP</span>`;
            }
        }

        const signalVal = isOnline ? `${dev.rssi} dBm` : 'N/A';
        const latencyVal = isOnline ? `${dev.latency} ms` : 'Disconnected';

        html += `
            <div class="${cardClass}">
                <div class="device-header">
                    <span class="device-id">${dev.id}</span>
                    <div style="display: flex; gap: 6px; align-items: center; flex-wrap: wrap;">
                        ${localBadge}
                        ${neighborBadge}
                        ${apBadge}
                        ${statusBadge}
                        <span class="device-type ${typeClass}">${dev.type}</span>
                    </div>
                </div>
                
                <div class="device-info">
                    <strong>${dev.name}</strong>
                    <span>IP: ${dev.ip}</span>
                    <span>Role: ${dev.role}</span>
                    <span>H/W: ${dev.hardware}</span>
                    ${dev.wifi_details ? `
                        <div class="wifi-hw-box" style="margin-top: 6px; padding: 6px 8px; background: rgba(15,23,42,0.85); border-radius: 6px; border: 1px solid rgba(0,229,255,0.25);">
                            <div style="font-size: 10px; font-weight: 800; color: #00e5ff; margin-bottom: 3px; display: flex; justify-content: space-between;">
                                <span>📻 NetMetal AX Radios (${dev.wifi_details.total_interfaces}):</span>
                                <span class="text-cyan">${dev.wifi_details.active_interfaces || 2} Active</span>
                            </div>
                            ${dev.wifi_details.interfaces.map(i => {
                                const isRun = i.running;
                                const isDis = i.disabled;
                                let badgeClass = isDis ? 'idle' : (isRun ? (i.mode === 'AP' ? 'publisher' : 'subscriber') : 'degraded');
                                let statusText = isDis ? 'DISABLED' : (isRun ? 'RUNNING' : 'INACTIVE (NO LINK)');
                                let statusLabel = i.flags ? `[${i.flags}] ${i.mode}` : i.mode;
                                if (i.ssid) statusLabel += ` (${i.ssid})`;
                                const colorHex = isRun ? '#f1f5f9' : (isDis ? '#64748b' : '#fbbf24');
                                return `
                                    <div style="font-size: 9.5px; color: ${colorHex}; display: flex; justify-content: space-between; align-items: center; margin-top: 3px;">
                                        <span>• <strong>${i.name}</strong> ${i.master ? `<small class="text-dim">(slave of ${i.master})</small>` : ''}</span>
                                        <span class="role-badge ${badgeClass}" style="font-size: 8px; padding: 1px 5px;">${statusLabel} • ${statusText}</span>
                                    </div>
                                `;
                            }).join('')}
                        </div>
                    ` : ''}
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
