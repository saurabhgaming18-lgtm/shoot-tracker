// Production Manager Web App Controller - Saurabh Patil Desk
let currentCategoryFilter = '';
let inventoryData = [];
let currentUploadedReceiptUrl = '';

// Official Lightpaper Creations Crew Members
const TEAM_MEMBERS = [
  "Rohit Salunke",
  "Vedant Mankar",
  "Akash Deshmukh",
  "Samyak Chavhan",
  "Saurabh Patil",
  "Riha Das",
  "Maulisha Guha"
];

function renderCrewChips(containerId, targetInputId) {
  const container = document.getElementById(containerId);
  const input = document.getElementById(targetInputId);
  if (!container || !input) return;

  const currentRaw = (input.value || "")
    .split(',')
    .map(s => s.trim())
    .filter(Boolean);

  container.innerHTML = TEAM_MEMBERS.map(name => {
    const isSelected = currentRaw.some(v => v.toLowerCase() === name.toLowerCase());
    return `
      <div class="crew-chip ${isSelected ? 'active' : ''}" 
           onclick="toggleCrewChip('${name}', '${targetInputId}', '${containerId}')"
           title="Click to ${isSelected ? 'remove' : 'assign'} ${name}">
        ${isSelected ? '✓ ' : '+ '}${name}
      </div>
    `;
  }).join('');
}

function toggleCrewChip(name, targetInputId, containerId) {
  const input = document.getElementById(targetInputId);
  if (!input) return;

  let currentList = (input.value || "")
    .split(',')
    .map(s => s.trim())
    .filter(Boolean);

  const idx = currentList.findIndex(x => x.toLowerCase() === name.toLowerCase());
  if (idx >= 0) {
    currentList.splice(idx, 1);
  } else {
    currentList.push(name);
  }

  input.value = currentList.join(', ');
  renderCrewChips(containerId, targetInputId);
}

// ----------------------------------------------------
// Registered Gear Inventory Equipment Selector (Strictly Authentic)
// ----------------------------------------------------
async function fetchAndGetEquipmentList() {
  if (!inventoryData || inventoryData.length === 0) {
    try {
      const res = await fetch('/api/inventory');
      if (res.ok) {
        inventoryData = await res.json();
      }
    } catch (e) {
      console.error("Error loading inventory:", e);
    }
  }

  // Strictly return authentic user-registered equipment from inventory
  const uniqueItems = [];
  (inventoryData || []).forEach(i => {
    const name = (i.name || '').trim();
    const model = (i.model || '').trim();
    let label = name;
    if (model && model.toLowerCase() !== name.toLowerCase()) {
      label = `${name} (${model})`;
    }
    if (label && !uniqueItems.includes(label)) {
      uniqueItems.push(label);
    }
  });

  return uniqueItems;
}

async function renderEquipmentChips(containerId, targetInputId) {
  const container = document.getElementById(containerId);
  const input = document.getElementById(targetInputId);
  if (!container || !input) return;

  const currentRaw = (input.value || "")
    .split(',')
    .map(s => s.trim())
    .filter(Boolean);

  const equipList = await fetchAndGetEquipmentList();

  if (equipList.length === 0) {
    container.innerHTML = `
      <div style="font-size: 11px; color: #94a3b8; padding: 4px 0;">
        ⚠️ <em>No inventory registered yet. Gear added in the <strong>Gear Inventory</strong> tab will automatically appear here.</em>
      </div>
    `;
    return;
  }

  container.innerHTML = equipList.map(item => {
    const isSelected = currentRaw.some(v => v.toLowerCase() === item.toLowerCase());
    return `
      <div class="crew-chip ${isSelected ? 'active' : ''}" 
           onclick="toggleEquipmentChip('${item.replace(/'/g, "\\'")}', '${targetInputId}', '${containerId}')"
           title="Click to ${isSelected ? 'remove' : 'add'} ${item}">
        ${isSelected ? '✓ ' : '+ '}${item}
      </div>
    `;
  }).join('');
}

function toggleEquipmentChip(item, targetInputId, containerId) {
  const input = document.getElementById(targetInputId);
  if (!input) return;

  let currentList = (input.value || "")
    .split(',')
    .map(s => s.trim())
    .filter(Boolean);

  const idx = currentList.findIndex(x => x.toLowerCase() === item.toLowerCase());
  if (idx >= 0) {
    currentList.splice(idx, 1);
  } else {
    currentList.push(item);
  }

  input.value = currentList.join(', ');
  renderEquipmentChips(containerId, targetInputId);
}

document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  initDates();
  initPasteScreenshotListener();
  refreshAllData();
});

// Setup date inputs to today's date
function initDates() {
  const today = new Date().toISOString().split('T')[0];
  const dateInputs = ['co-expected-return', 'brf-date', 'exp-date'];
  dateInputs.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = today;
  });

  const liveBadge = document.getElementById('live-date-badge');
  if (liveBadge) {
    const d = new Date();
    const formatted = d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
    liveBadge.textContent = `📅 ${formatted} (Active Tracking)`;
  }
}

// Screenshot Paste (Ctrl + V) Handler
function initPasteScreenshotListener() {
  window.addEventListener('paste', async (e) => {
    const modalExpense = document.getElementById('modal-expense');
    if (!modalExpense || !modalExpense.classList.contains('active')) return;

    const items = (e.clipboardData || e.originalEvent.clipboardData).items;
    for (let item of items) {
      if (item.type.indexOf('image') === 0) {
        const blob = item.getAsFile();
        await uploadReceiptBlob(blob, 'pasted_screenshot.png');
        break;
      }
    }
  });
}

// Navigation Tabs
function initTabs() {
  document.querySelectorAll('.nav-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      const target = tab.getAttribute('data-tab');
      switchTab(target);
    });
  });
}

async function switchTab(tabId) {
  document.querySelectorAll('.nav-tab').forEach(t => {
    t.classList.toggle('active', t.getAttribute('data-tab') === tabId);
  });
  document.querySelectorAll('.tab-pane').forEach(p => {
    p.classList.toggle('active', p.id === `tab-${tabId}`);
  });
  
  try {
    if (tabId === 'inventory') {
      await loadInventory();
    } else if (tabId === 'dispatch') {
      await loadDispatches();
    } else if (tabId === 'briefs') {
      await loadBriefs();
    } else if (tabId === 'expenses') {
      await loadExpenses();
    } else if (tabId === 'dashboard') {
      await refreshAllData();
    }
  } catch (e) {
    console.error("Error switching tab:", e);
  }
}

// Master Refresh
async function refreshAllData() {
  try {
    const res = await fetch('/api/dashboard');
    if (!res.ok) return;
    const data = await res.json();
    
    // Top stats
    const availEl = document.getElementById('stat-available');
    if (availEl) availEl.textContent = data.equipment.available_items || 0;
    
    const inUseEl = document.getElementById('stat-in-use');
    if (inUseEl) inUseEl.textContent = data.equipment.in_use_items || 0;
    
    const activeShootsEl = document.getElementById('stat-active-shoots');
    if (activeShootsEl) activeShootsEl.textContent = data.equipment.active_dispatches || 0;
    
    const pettyCashEl = document.getElementById('stat-petty-cash');
    if (pettyCashEl) pettyCashEl.textContent = `₹${(data.expenses.total_expenses || 0).toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
    
    const pettySubEl = document.getElementById('stat-petty-sub');
    if (pettySubEl) pettySubEl.textContent = `${data.expenses.transaction_count || 0} Receipts Logged`;

    // Active Dispatches (Dashboard)
    renderActiveDispatches(data.active_dispatches);

    // Latest Shoot (Shoot Tracker)
    renderDashboardLatestBrief(data.latest_brief);

    // Live On-Set Shoot Monitor (Desktop Real-time Stream)
    try { await loadDesktopLiveShootsDropdown(); } catch (e) { console.error("Error loading live on-set stream:", e); }

    // Safely load all sub-tabs independently with try-catch protection
    try { await loadInventory(); } catch (e) { console.error("Error loading inventory:", e); }
    try { await loadDispatches(); } catch (e) { console.error("Error loading dispatches:", e); }
    try { await loadBriefs(); } catch (e) { console.error("Error loading briefs:", e); }
    try { await loadExpenses(); } catch (e) { console.error("Error loading expenses:", e); }

  } catch (err) {
    console.error("Error refreshing dashboard:", err);
  }
}

// ----------------------------------------------------
// Live On-Set Shoot Tracker Stream (Desktop Dashboard)
// ----------------------------------------------------
let activeDesktopLiveShootId = null;

async function loadDesktopLiveShootsDropdown() {
  try {
    const res = await fetch('/api/tracker/shoots');
    if (!res.ok) return;
    const shoots = await res.json();
    const select = document.getElementById('desktop-live-shoot-select');
    if (!select) return;

    if (shoots.length === 0) {
      select.innerHTML = '<option value="">No Active Shoots</option>';
      return;
    }

    select.innerHTML = shoots.map(s => `
      <option value="${s.id}" ${s.id === activeDesktopLiveShootId ? 'selected' : ''}>
        ${s.project_name} (${s.shoot_date || 'Date TBD'}) - ${s.client || 'Client'}
      </option>
    `).join('');

    if (!activeDesktopLiveShootId || !shoots.some(s => s.id === activeDesktopLiveShootId)) {
      activeDesktopLiveShootId = shoots[0].id;
      select.value = activeDesktopLiveShootId;
    }

    await loadDesktopLiveShoot(activeDesktopLiveShootId);
  } catch (e) {
    console.error("Error loading desktop live shoots dropdown:", e);
  }
}

async function loadDesktopLiveShoot(shootId) {
  if (!shootId) return;
  activeDesktopLiveShootId = shootId;

  try {
    const res = await fetch(`/api/tracker/shoot/${shootId}`);
    if (!res.ok) return;
    const data = await res.json();

    const b = data.brief || {};
    // Box 1: Mission & Milestones
    const shootNameEl = document.getElementById('desk-live-shoot-name');
    if (shootNameEl) shootNameEl.textContent = `Mission: ${b.project_name || 'Production'}`;
    const callTimeEl = document.getElementById('desk-live-call-time');
    if (callTimeEl) callTimeEl.textContent = `⏰ Call: ${b.call_time || '--'}`;
    const locEl = document.getElementById('desk-live-location');
    if (locEl) locEl.innerHTML = `📍 Location: <strong>${b.location || 'Studio Set'}</strong>`;

    const milestoneTypes = (data.milestones || []).map(m => m.type);
    const msLabels = [
      { type: 'reached_office', label: '🏢 Office' },
      { type: 'call_checkin', label: '📍 Set Call' },
      { type: 'setup_complete', label: '⚡ Setup' },
      { type: 'waiting', label: '⏳ Waiting' },
      { type: 'first_shot', label: '🎬 1st Shot' },
      { type: 'lunch_call', label: '🍱 Lunch' },
      { type: 'lunch_resume', label: '🔄 Resumed' },
      { type: 'wrap_call', label: '🎉 Wrap' }
    ];

    const msGrid = document.getElementById('desk-live-milestones-grid');
    if (msGrid) {
      msGrid.innerHTML = msLabels.map(m => {
        const isDone = milestoneTypes.includes(m.type);
        const item = (data.milestones || []).find(x => x.type === m.type);
        const timeStr = item ? item.time_str : '';
        return `
          <div style="background: ${isDone ? 'rgba(34, 197, 94, 0.15)' : 'rgba(255,255,255,0.04)'}; border: 1px solid ${isDone ? '#22c55e' : 'rgba(255,255,255,0.08)'}; border-radius: 6px; padding: 6px 4px; text-align: center;">
            <div style="font-size: 11px; font-weight: 700; color: ${isDone ? '#4ade80' : '#94a3b8'};">${m.label}</div>
            <div style="font-size: 10px; color: ${isDone ? '#22c55e' : '#64748b'};">${isDone ? (timeStr || 'Done') : 'Pending'}</div>
          </div>
        `;
      }).join('');
    }

    // Box 2: Takes stream
    const takes = data.shots || [];
    const takesCountEl = document.getElementById('desk-live-takes-count');
    if (takesCountEl) takesCountEl.textContent = takes.length;

    const takesStreamEl = document.getElementById('desk-live-takes-stream');
    if (takesStreamEl) {
      if (takes.length === 0) {
        takesStreamEl.innerHTML = `<div style="text-align: center; color: #64748b; padding: 20px;">No takes logged on set yet today.</div>`;
      } else {
        const reversed = [...takes].reverse();
        takesStreamEl.innerHTML = reversed.map(t => {
          const isGood = t.is_circle || t.status === 'Good';
          return `
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
              <div>
                <strong style="color: #f59e0b;">Sc ${t.scene} • Sh ${t.shot} • Tk ${t.take}</strong>
                <span class="badge ${isGood ? 'badge-available' : 'badge-in-use'}" style="margin-left: 6px; font-size: 9px; padding: 2px 6px;">${isGood ? '⭐ Good' : 'NG'}</span>
                <div style="color: #cbd5e1; font-size: 11px;">${t.notes || '<em style="color:#64748b;">No notes</em>'}</div>
              </div>
              <div style="text-align: right; font-size: 10px; color: #94a3b8;">
                <div>${t.time_str || ''}</div>
                <div>${t.crew_name || 'Crew'}</div>
              </div>
            </div>
          `;
        }).join('');
      }
    }

    // Box 3: Gear checklist status & live activity
    const gearList = data.gear_checklist || [];
    const packedCount = gearList.filter(g => g.packed).length;
    const onSetCount = gearList.filter(g => g.on_set).length;
    const returnedCount = gearList.filter(g => g.returned).length;
    const damagedCount = gearList.filter(g => g.damaged).length;

    const gearRatioEl = document.getElementById('desk-live-gear-ratio');
    if (gearRatioEl) {
      gearRatioEl.textContent = `${onSetCount} / ${gearList.length} on Set`;
    }

    const gearBarsEl = document.getElementById('desk-live-gear-bars');
    if (gearBarsEl) {
      gearBarsEl.innerHTML = `
        <span class="badge" style="background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); font-size: 11px;">📦 Packed: ${packedCount}/${gearList.length}</span>
        <span class="badge badge-available" style="font-size: 11px;">📍 On Set: ${onSetCount}/${gearList.length}</span>
        <span class="badge" style="background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3); font-size: 11px;">🔒 Returned: ${returnedCount}/${gearList.length}</span>
        ${damagedCount > 0 ? `<span class="badge badge-maintenance" style="font-size: 11px;">⚠️ Issues: ${damagedCount}</span>` : ''}
      `;
    }

    const activity = data.activity || [];
    const actStreamEl = document.getElementById('desk-live-activity-stream');
    if (actStreamEl) {
      if (activity.length === 0) {
        actStreamEl.innerHTML = `<div style="text-align: center; color: #64748b; padding: 10px;">Awaiting live crew activity...</div>`;
      } else {
        actStreamEl.innerHTML = activity.slice(0, 5).map(a => `
          <div style="display: flex; justify-content: space-between; gap: 8px; padding: 3px 0; color: #cbd5e1; font-size: 11px; border-bottom: 1px solid rgba(255,255,255,0.03);">
            <div><strong>${a.crew_name}:</strong> ${a.action} <span style="color:#94a3b8;">${a.details ? '(' + a.details + ')' : ''}</span></div>
            <div style="color: #64748b; font-size: 10px; white-space: nowrap;">${a.time_str || ''}</div>
          </div>
        `).join('');
      }
    }

  } catch (e) {
    console.error("Error loading desktop live shoot details:", e);
  }
}

async function refreshDesktopLiveTracker() {
  if (activeDesktopLiveShootId) {
    await loadDesktopLiveShoot(activeDesktopLiveShootId);
  } else {
    await loadDesktopLiveShootsDropdown();
  }
}

// Clear all data handler
async function confirmClearAllData() {
  if (!confirm("Are you sure you want to clear all data in the dashboard and spreadsheet?")) {
    return;
  }
  const res = await fetch('/api/clear_all', { method: 'POST' });
  if (res.ok) {
    await refreshAllData();
    alert("🧹 Dashboard and Master Spreadsheet cleared cleanly!");
  }
}

// ----------------------------------------------------
// Active Dispatches (Dashboard)
// ----------------------------------------------------
function renderActiveDispatches(logs) {
  const tbody = document.getElementById('dashboard-active-dispatches-body');
  if (!tbody) return;
  if (!logs || logs.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding: 20px; color: #94a3b8;">No equipment currently on the field. All gear is checked in!</td></tr>`;
    return;
  }

  tbody.innerHTML = logs.map(l => `
    <tr>
      <td><strong style="color: #38bdf8;">${l.id}</strong></td>
      <td><strong>${l.project_name}</strong></td>
      <td>${l.assigned_crew}</td>
      <td>${l.date_out} ${l.time_out}</td>
      <td><span style="color: #facc15;">${l.expected_return}</span></td>
      <td style="max-width: 250px; font-size: 12px; color: #94a3b8;">${l.items_summary}</td>
      <td><span class="badge badge-in-use">Active Out</span></td>
      <td>
        <div style="display: flex; gap: 6px; align-items: center;">
          <button class="btn btn-success" style="padding: 4px 10px; font-size: 11px;" onclick="openCheckinModal('${l.id}', '${l.project_name}', '${l.assigned_crew}')">📥 Check In</button>
          <button class="btn btn-outline" style="padding: 4px 8px; font-size: 11px; color: #ef4444; border-color: rgba(239, 68, 68, 0.3); cursor: pointer;" onclick="deleteDispatch('${l.id}')" title="Delete Dispatch Log">🗑️</button>
        </div>
      </td>
    </tr>
  `).join('');
}

// ----------------------------------------------------
// Inventory Tab
// ----------------------------------------------------
async function loadInventory() {
  const res = await fetch('/api/inventory');
  if (res.ok) {
    inventoryData = await res.json();
    renderInventoryTable();
    populateCheckoutOptions();
  }
}

function filterInventory(cat) {
  currentCategoryFilter = cat;
  document.querySelectorAll('#inventory-filter-chips .chip-btn').forEach(btn => {
    btn.classList.toggle('active', btn.textContent.trim().toLowerCase().includes(cat.toLowerCase()) || (cat === '' && btn.textContent.includes('All')));
  });
  renderInventoryTable();
}

function renderInventoryTable() {
  const tbody = document.getElementById('inventory-table-body');
  if (!tbody) return;
  let items = inventoryData;
  if (currentCategoryFilter) {
    items = items.filter(i => (i.category || '').toLowerCase() === currentCategoryFilter.toLowerCase());
  }

  if (items.length === 0) {
    tbody.innerHTML = `<tr><td colspan="10" style="text-align:center; padding: 24px; color: #94a3b8;">No equipment registered yet. Click "📁 Import Equipment List (CSV)" or "+ Add Gear Item" to start.</td></tr>`;
    return;
  }

  tbody.innerHTML = items.map(i => {
    const statusClass = i.status === 'Available' ? 'badge-available' : (i.status === 'In Use' ? 'badge-in-use' : 'badge-maintenance');
    return `
      <tr>
        <td><strong>${i.id}</strong></td>
        <td><span class="badge" style="background: rgba(255,255,255,0.06);">${i.category}</span></td>
        <td><strong>${i.name}</strong></td>
        <td style="color: #94a3b8;">${i.model || '--'}</td>
        <td style="font-family: monospace; font-size: 11px;">${i.serial || 'N/A'}</td>
        <td>${i.location || 'Studio'}</td>
        <td style="text-align: center;">${i.quantity || 1}</td>
        <td><span class="badge ${statusClass}">${i.status}</span></td>
        <td style="font-size: 12px; color: #94a3b8;">${i.notes || '--'}</td>
        <td>
          <button class="btn btn-outline" style="padding: 4px 8px; font-size: 11px; color: #ef4444;" onclick="deleteItem('${i.id}')">🗑️</button>
        </td>
      </tr>
    `;
  }).join('');
}

function populateCheckoutOptions() {
  const select = document.getElementById('co-items');
  if (!select) return;
  const avail = inventoryData.filter(i => i.status === 'Available');
  if (avail.length === 0) {
    select.innerHTML = `<option value="General Gear" selected>Custom Gear Entry (Describe in notes)</option>`;
    return;
  }
  select.innerHTML = avail.map(i => `
    <option value="${i.id}">[${i.id}] ${i.name} (${i.category})</option>
  `).join('');
}

// ----------------------------------------------------
// Dispatches Tab
// ----------------------------------------------------
async function loadDispatches() {
  const res = await fetch('/api/dispatches');
  if (res.ok) {
    const logs = await res.json();
    const tbody = document.getElementById('dispatch-table-body');
    if (!tbody) return;
    if (logs.length === 0) {
      tbody.innerHTML = `<tr><td colspan="11" style="text-align:center; padding: 24px; color: #94a3b8;">No dispatch records found. Click "+ Check-Out Equipment" to create one.</td></tr>`;
      return;
    }

    tbody.innerHTML = logs.map(l => {
      const isOut = l.status === 'Active Out';
      const statusBadge = isOut ? '<span class="badge badge-in-use">Active Out</span>' :
        (l.status === 'Returned Clean' ? '<span class="badge badge-returned-clean">Returned Clean</span>' : '<span class="badge badge-maintenance">Returned with Issues</span>');
      
      return `
        <tr>
          <td><strong style="color: #38bdf8;">${l.id}</strong></td>
          <td>${l.date_out} ${l.time_out}</td>
          <td><strong>${l.project_name}</strong></td>
          <td>${l.assigned_crew}</td>
          <td style="max-width: 250px; font-size: 12px;">${l.items_summary}</td>
          <td style="color: #94a3b8; font-size: 12px;">${l.condition_out}</td>
          <td><span style="color: #facc15;">${l.expected_return}</span></td>
          <td style="color: #94a3b8; font-size: 12px;">${l.actual_return}</td>
          <td style="color: #94a3b8; font-size: 12px;">${l.condition_in}</td>
          <td>${statusBadge}</td>
          <td>
            <div style="display: flex; gap: 6px; align-items: center;">
              ${isOut ? `<button class="btn btn-success" style="padding: 4px 8px; font-size: 11px;" onclick="openCheckinModal('${l.id}', '${l.project_name}', '${l.assigned_crew}')">📥 Return</button>` : ''}
              <button class="btn btn-outline" style="padding: 4px 8px; font-size: 11px; color: #ef4444; border-color: rgba(239, 68, 68, 0.3); cursor: pointer;" onclick="deleteDispatch('${l.id}')" title="Delete Dispatch Log">🗑️</button>
            </div>
          </td>
        </tr>
      `;
    }).join('');
  }
}


// ----------------------------------------------------
// Shoot Status Helpers & Custom Status Handler
// ----------------------------------------------------
function getStatusClass(status) {
  const s = (status || '').toLowerCase().trim();
  if (s === 'active') return 'status-pill-active';
  if (s === 'scheduled') return 'status-pill-scheduled';
  if (s === 'in progress' || s === 'in-progress' || s === 'rolling') return 'status-pill-in-progress';
  if (s === 'wrapped' || s === 'wrap' || s === 'camera wrap') return 'status-pill-wrapped';
  if (s === 'post-production' || s === 'post production' || s === 'post') return 'status-pill-post-production';
  if (s === 'completed' || s === 'delivered' || s === 'done') return 'status-pill-completed';
  if (s === 'postponed' || s === 'delayed') return 'status-pill-postponed';
  if (s === 'cancelled' || s === 'canceled') return 'status-pill-cancelled';
  return 'status-pill-custom';
}

function getStatusOptionsHtml(currentStatus) {
  const cur = (currentStatus || 'Active').trim();
  const presets = ['Active', 'Scheduled', 'In Progress', 'Wrapped', 'Post-Production', 'Completed', 'Postponed', 'Cancelled'];
  const isCustom = cur && !presets.some(p => p.toLowerCase() === cur.toLowerCase());

  let html = '';
  if (isCustom) {
    html += `<option value="${cur}" selected>✨ ${cur}</option>`;
  }

  const statuses = [
    { val: 'Active', label: '🟢 Active' },
    { val: 'Scheduled', label: '🟡 Scheduled' },
    { val: 'In Progress', label: '🔵 In Progress' },
    { val: 'Wrapped', label: '🟣 Wrapped' },
    { val: 'Post-Production', label: '🟠 Post-Prod' },
    { val: 'Completed', label: '✅ Completed' },
    { val: 'Postponed', label: '⏸️ Postponed' },
    { val: 'Cancelled', label: '❌ Cancelled' }
  ];

  statuses.forEach(s => {
    const isSel = !isCustom && s.val.toLowerCase() === cur.toLowerCase();
    html += `<option value="${s.val}" ${isSel ? 'selected' : ''}>${s.label}</option>`;
  });

  html += `<option value="__custom__">✏️ + Custom Status (Type Name)...</option>`;
  return html;
}

async function changeShootStatus(briefId, newStatus, selectEl) {
  if (!briefId) return;

  if (newStatus === '__custom__') {
    const prev = selectEl ? (selectEl.getAttribute('data-prev') || 'Active') : 'Active';
    if (selectEl) selectEl.value = prev;
    openCustomStatusModal(briefId, prev);
    return;
  }

  if (selectEl) {
    selectEl.setAttribute('data-prev', newStatus);
    selectEl.className = `status-pill-select ${getStatusClass(newStatus)}`;
  }

  try {
    const res = await fetch(`/api/briefs/${encodeURIComponent(briefId)}/status`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus })
    });

    if (res.ok) {
      showStatusToast(`🎯 Shoot <strong>${briefId}</strong> status changed to <strong>"${newStatus}"</strong>! Master Excel synced.`);
      await loadBriefs();
      const dashRes = await fetch('/api/dashboard');
      if (dashRes.ok) {
        const data = await dashRes.json();
        renderDashboardLatestBrief(data.latest_brief);
      }
    } else {
      const err = await res.json().catch(() => ({}));
      alert(`⚠️ Failed to update status: ${err.detail || 'Server error'}`);
      await loadBriefs();
    }
  } catch (err) {
    console.error("Error updating shoot status:", err);
    alert("Connection error while updating status.");
  }
}

function openCustomStatusModal(shootId, currentStatus, projName) {
  document.getElementById('custom-status-shoot-id').value = shootId;
  const infoEl = document.getElementById('custom-status-shoot-info');
  if (infoEl) {
    infoEl.textContent = `${shootId} ${projName ? '• ' + projName : ''}`;
  }
  const inputEl = document.getElementById('custom-status-input');
  if (inputEl) {
    inputEl.value = (currentStatus && currentStatus !== '__custom__') ? currentStatus : '';
  }
  openModal('modal-custom-status');
  setTimeout(() => inputEl?.focus(), 100);
}

function setCustomStatusInput(val) {
  const inputEl = document.getElementById('custom-status-input');
  if (inputEl) {
    inputEl.value = val;
    inputEl.focus();
  }
}

async function submitCustomStatusModal(e) {
  e.preventDefault();
  const shootId = document.getElementById('custom-status-shoot-id').value;
  const customStatus = document.getElementById('custom-status-input').value.trim();
  if (!shootId || !customStatus) return;

  closeModal('modal-custom-status');
  await changeShootStatus(shootId, customStatus, null);
}

function renderDashboardLatestBrief(latestBrief) {
  const briefContainer = document.getElementById('dashboard-latest-brief');
  if (!briefContainer) return;
  if (latestBrief) {
    const equip = latestBrief.equipment_manifest || latestBrief.equipment_for_shoot || 'Standard Kit';
    const crew = latestBrief.cast_talent || latestBrief.key_contacts || 'Camera Crew';
    const contactPerson = latestBrief.contact_person ? ` (POC: ${latestBrief.contact_person})` : '';

    briefContainer.innerHTML = `
      <div style="background: linear-gradient(135deg, rgba(24, 34, 58, 0.7) 0%, rgba(13, 20, 36, 0.85) 100%); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 14px; padding: 20px; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.5);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; flex-wrap: wrap; gap: 8px;">
          <div>
            <span style="font-family: var(--font-mono); font-size: 11px; color: #38bdf8; font-weight: 700; background: rgba(56, 189, 248, 0.12); padding: 3px 8px; border-radius: 4px; border: 1px solid rgba(56, 189, 248, 0.3);">${latestBrief.id}</span>
            <strong style="color: #ffffff; font-family: var(--font-display); font-size: 17px; margin-left: 8px;">${latestBrief.project_name}</strong>
          </div>
          <div class="status-pill-container">
            <select class="status-pill-select ${getStatusClass(latestBrief.status)}" data-prev="${latestBrief.status}" onchange="changeShootStatus('${latestBrief.id}', this.value, this)" title="Click to change shoot status">
              ${getStatusOptionsHtml(latestBrief.status)}
            </select>
          </div>
        </div>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 14px; margin-bottom: 16px; font-size: 12px; line-height: 1.6;">
          <div>
            <strong style="color: #94a3b8; text-transform: uppercase; font-size: 10px; letter-spacing: 0.05em; display: block;">Client & POC</strong>
            <span style="color: #f8fafc; font-weight: 600;">${latestBrief.client}${contactPerson}</span>
          </div>
          <div>
            <strong style="color: #94a3b8; text-transform: uppercase; font-size: 10px; letter-spacing: 0.05em; display: block;">Shoot Date & Reach Time</strong>
            <span style="color: #facc15; font-weight: 700;">📅 ${latestBrief.shoot_date} &nbsp;•&nbsp; ⏰ ${latestBrief.call_time}</span>
          </div>
          <div>
            <strong style="color: #94a3b8; text-transform: uppercase; font-size: 10px; letter-spacing: 0.05em; display: block;">Location</strong>
            <span style="color: #f8fafc; font-weight: 500;">📍 ${latestBrief.location}</span>
          </div>
          <div>
            <strong style="color: #94a3b8; text-transform: uppercase; font-size: 10px; letter-spacing: 0.05em; display: block;">Assigned Crew</strong>
            <span style="color: #38bdf8; font-weight: 600;">👥 ${crew}</span>
          </div>
          <div style="grid-column: 1 / -1; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 8px;">
            <strong style="color: #94a3b8; text-transform: uppercase; font-size: 10px; letter-spacing: 0.05em; display: block;">Equipment for Shoot</strong>
            <span style="color: #38bdf8; font-weight: 600;">🎥 ${equip}</span>
          </div>
        </div>

        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
          <a href="/api/brief/print/${latestBrief.id}" target="_blank" class="btn btn-outline" style="padding: 6px 12px; font-size: 12px;">📄 View Call Sheet</a>
          <a href="/api/brief/checklist/${latestBrief.id}" target="_blank" class="btn btn-outline" style="padding: 6px 12px; font-size: 12px; color: #38bdf8; border-color: rgba(56, 189, 248, 0.45); background: rgba(56,189,248,0.08);">📋 Crew Checklist</a>
          ${latestBrief.is_editable ? `<button class="btn btn-outline" style="padding: 6px 12px; font-size: 12px; color: #facc15; border-color: rgba(250, 204, 21, 0.45);" onclick="openEditBriefModal('${latestBrief.id}')">✏️ Edit Shoot</button>` : ''}
          <button class="btn btn-outline" style="padding: 6px 12px; font-size: 12px; color: #22c55e; border-color: rgba(34, 197, 94, 0.45);" onclick="shareShootWhatsApp('${latestBrief.id}')">📲 WhatsApp</button>
          <button class="btn btn-outline" style="padding: 6px 12px; font-size: 12px; color: #38bdf8; border-color: rgba(56, 189, 248, 0.45);" onclick="copyShootWhatsAppText('${latestBrief.id}')">📋 Copy Note</button>
          <a href="/api/brief/download/${latestBrief.id}" class="btn btn-primary" style="padding: 6px 14px; font-size: 12px;">📥 Download</a>
        </div>
      </div>
    `;
  } else {
    briefContainer.innerHTML = `<div style="color: #94a3b8; font-size: 13px; padding: 16px; text-align: center;">No shoots logged in Shoot Tracker yet.</div>`;
  }
}

function showStatusToast(message) {
  const existing = document.querySelector('.status-toast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.className = 'status-toast';
  toast.innerHTML = `<span>✨</span><span>${message}</span>`;
  document.body.appendChild(toast);

  setTimeout(() => {
    toast.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(20px)';
    setTimeout(() => toast.remove(), 400);
  }, 3200);
}

// ----------------------------------------------------
// Shoot Tracker Tab
// ----------------------------------------------------
async function loadBriefs() {
  const res = await fetch('/api/briefs');
  if (res.ok) {
    const briefs = await res.json();
    const tbody = document.getElementById('briefs-table-body');
    if (!tbody) return;
    if (briefs.length === 0) {
      tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; padding: 24px; color: #94a3b8;">No shoots logged in Shoot Tracker. Click "+ Add New Shoot" to plan one.</td></tr>`;
      return;
    }

    tbody.innerHTML = briefs.map(b => {
      const clientPOC = `
        <div style="font-weight: 700;">${b.client || 'Client'}</div>
        ${b.contact_person ? `<div style="font-size: 11px; color: #94a3b8; margin-top: 2px;">👤 ${b.contact_person}</div>` : ''}
      `;

      const deliverablesText = b.deliverables || b.concept || 'Shoot Coverage & Deliverables';

      const editBtn = b.is_editable ? `
        <button class="btn btn-outline" style="padding: 4px 8px; font-size: 11px; color: #facc15; border-color: rgba(250, 204, 21, 0.4); cursor: pointer;" onclick="openEditBriefModal('${b.id}')" title="Edit Shoot (Same-Day Window Active)">✏️ Edit</button>
      ` : `
        <button class="btn btn-outline" style="padding: 4px 8px; font-size: 11px; color: #64748b; border-color: rgba(100, 116, 139, 0.3); opacity: 0.6; cursor: not-allowed;" onclick="alert('🔒 Editing is locked for this shoot.\\n\\nPolicy: Changes are only accepted on the same day of entry (Created: ${b.created_date || b.created_at || b.shoot_date}). Next-day edits are locked for production & audit integrity.')" title="Editing Locked (Next-Day Policy)">🔒 Locked</button>
      `;

      const statusCell = `
        <div class="status-pill-container" style="display: flex; align-items: center; gap: 4px;">
          <select class="status-pill-select ${getStatusClass(b.status)}" data-prev="${b.status}" onchange="changeShootStatus('${b.id}', this.value, this)" title="Click to change shoot status">
            ${getStatusOptionsHtml(b.status)}
          </select>
          <button type="button" class="btn btn-outline" style="padding: 3px 6px; font-size: 10px; border-radius: 4px; color: #94a3b8; border-color: rgba(255,255,255,0.1);" onclick="openCustomStatusModal('${b.id}', '${b.status}', '${(b.project_name || '').replace(/'/g, "\\'")}')" title="Type custom status">✏️</button>
        </div>
      `;

      return `
        <tr>
          <td><strong style="color: #eab308; font-size: 13px;">${b.id}</strong></td>
          <td><strong style="color: #f1f5f9;">${b.project_name}</strong></td>
          <td>${clientPOC}</td>
          <td style="max-width: 220px; font-size: 12px; color: #38bdf8; line-height: 1.4;">${deliverablesText}</td>
          <td style="white-space: nowrap; font-size: 13px;">
            📅 ${b.shoot_date}
            ${b.shoot_end_date && b.shoot_end_date !== b.shoot_date ? `<div style="font-size: 11px; color: #94a3b8; margin-top: 2px;">→ ${b.shoot_end_date}</div>` : ''}
          </td>
          <td><strong style="color: #facc15; font-size: 13px;">${b.call_time}</strong></td>
          <td style="font-size: 12px; max-width: 200px;">📍 ${b.location}</td>
          <td>${statusCell}</td>
          <td>
            <div style="display: flex; gap: 6px; flex-wrap: wrap;">
              <a href="/api/brief/print/${b.id}" target="_blank" class="btn btn-outline" style="padding: 4px 8px; font-size: 11px;">📄 Call Sheet</a>
              <a href="/api/brief/checklist/${b.id}" target="_blank" class="btn btn-outline" style="padding: 4px 8px; font-size: 11px; color: #38bdf8; border-color: rgba(56, 189, 248, 0.4); cursor: pointer;" title="Print 2-Stage Camera Crew Equipment Checklist">📋 Checklist</a>
              ${editBtn}
              <button class="btn btn-outline" style="padding: 4px 8px; font-size: 11px; color: #22c55e; border-color: rgba(34, 197, 94, 0.4); cursor: pointer;" onclick="shareShootWhatsApp('${b.id}')" title="Share on WhatsApp">📲 WhatsApp</button>
              <button class="btn btn-outline" style="padding: 4px 8px; font-size: 11px; color: #38bdf8; border-color: rgba(56, 189, 248, 0.4); cursor: pointer;" onclick="copyShootWhatsAppText('${b.id}')" title="Copy Text for WhatsApp">📋 Copy</button>
              <a href="/api/brief/download/${b.id}" class="btn btn-primary" style="padding: 4px 8px; font-size: 11px;">📥 Download</a>
              <button class="btn btn-outline" style="padding: 4px 8px; font-size: 11px; color: #ef4444; border-color: rgba(239, 68, 68, 0.3); cursor: pointer;" onclick="deleteShoot('${b.id}')" title="Delete Shoot">🗑️</button>
            </div>
          </td>
        </tr>
      `;
    }).join('');
  }
}

// ----------------------------------------------------
// Expenses Tab with Receipt Images
// ----------------------------------------------------
async function loadExpenses() {
  const res = await fetch('/api/expenses');
  if (res.ok) {
    const expenses = await res.json();
    const tbody = document.getElementById('expenses-table-body');
    if (!tbody) return;
    if (expenses.length === 0) {
      tbody.innerHTML = `<tr><td colspan="11" style="text-align:center; padding: 24px; color: #94a3b8;">No expenses logged yet. Click "+ Add Expense & Attach Bill" to track on-set costs.</td></tr>`;
      return;
    }

    tbody.innerHTML = expenses.map(e => {
      const receiptCell = e.receipt_image ? `
        <img src="${e.receipt_image}" class="receipt-thumb" onclick="openLightbox('${e.receipt_image}', '${e.description}')" title="Click to view full receipt">
      ` : `<span style="color: #64748b; font-size: 11px;">No bill</span>`;

      return `
        <tr>
          <td><strong style="color: #38bdf8;">${e.id}</strong></td>
          <td>${e.date}</td>
          <td><strong>${e.project_name}</strong></td>
          <td><span class="badge" style="background: rgba(255,255,255,0.06);">${e.category}</span></td>
          <td style="font-size: 13px;">${e.description}</td>
          <td style="font-weight: 700; color: #4ade80;">₹${Number(e.amount).toLocaleString('en-IN', {minimumFractionDigits: 2})}</td>
          <td>${receiptCell}</td>
          <td>${e.paid_by}</td>
          <td><span class="badge" style="background: rgba(56,189,248,0.1); color: #38bdf8;">${e.mode}</span></td>
          <td><span class="badge badge-approved">${e.status}</span></td>
          <td>
            <button class="btn btn-outline" style="padding: 4px 8px; font-size: 11px; color: #ef4444;" onclick="deleteExpense('${e.id}')">🗑️</button>
          </td>
        </tr>
      `;
    }).join('');
  }
}

// ----------------------------------------------------
// Receipt / Screenshot Upload Logic
// ----------------------------------------------------
async function handleReceiptFileSelect(event) {
  const file = event.target.files[0];
  if (file) {
    await uploadReceiptBlob(file, file.name);
  }
}

async function uploadReceiptBlob(blob, filename) {
  const formData = new FormData();
  formData.append('file', blob, filename || 'receipt.jpg');

  try {
    const res = await fetch('/api/expenses/upload_receipt', {
      method: 'POST',
      body: formData
    });
    if (res.ok) {
      const data = await res.json();
      currentUploadedReceiptUrl = data.url;
      document.getElementById('exp-receipt-url').value = data.url;
      
      const previewImg = document.getElementById('exp-preview-img');
      previewImg.src = data.url;
      previewImg.style.display = 'block';
    }
  } catch (err) {
    alert("Error uploading receipt image.");
  }
}

// Lightbox Viewer
function openLightbox(imgUrl, desc) {
  document.getElementById('lightbox-img').src = imgUrl;
  document.getElementById('lightbox-title').textContent = `📷 Receipt: ${desc || 'Attached Bill'}`;
  document.getElementById('lightbox-download-link').href = imgUrl;
  openModal('modal-lightbox');
}

// ----------------------------------------------------
// Modals Open & Close
// ----------------------------------------------------
function openModal(id) {
  const m = document.getElementById(id);
  if (m) m.classList.add('active');
}
function closeModal(id) {
  const m = document.getElementById(id);
  if (m) m.classList.remove('active');
}

function openCheckoutModal() {
  populateCheckoutOptions();
  renderCrewChips('co-crew-chips', 'co-crew');
  openModal('modal-checkout');
}

function openCheckinModal(dispId, projName, crew) {
  document.getElementById('ci-dispatch-id').value = dispId;
  document.getElementById('ci-disp-info').textContent = `Dispatch ID: ${dispId} | ${projName} (${crew})`;
  document.getElementById('ci-damaged-notes').value = '';
  openModal('modal-checkin');
}

function openBriefModal() {
  renderCrewChips('brf-crew-chips', 'brf-team');
  renderEquipmentChips('brf-equipment-chips', 'brf-equipment');
  openModal('modal-brief');
}

function openExpenseModal() {
  currentUploadedReceiptUrl = '';
  document.getElementById('exp-receipt-url').value = '';
  const preview = document.getElementById('exp-preview-img');
  if (preview) {
    preview.src = '';
    preview.style.display = 'none';
  }
  openModal('modal-expense');
}

function openAddItemModal() {
  openModal('modal-add-item');
}

function openImportModal() {
  openModal('modal-import');
}

// ----------------------------------------------------
// Form Submissions
// ----------------------------------------------------
async function submitCheckout(e) {
  e.preventDefault();
  const select = document.getElementById('co-items');
  const selectedItems = Array.from(select.selectedOptions).map(o => o.value);

  const payload = {
    project_name: document.getElementById('co-project').value,
    assigned_crew: document.getElementById('co-crew').value,
    item_ids: selectedItems.length > 0 ? selectedItems : ["General Kit"],
    expected_return: document.getElementById('co-expected-return').value,
    condition_out: document.getElementById('co-condition').value || "Good / Tested",
    notes: document.getElementById('co-notes').value
  };

  const res = await fetch('/api/checkout', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });

  if (res.ok) {
    closeModal('modal-checkout');
    await refreshAllData();
    alert("✅ Equipment dispatched and logged into Master Spreadsheet!");
  } else {
    alert("Failed to dispatch equipment.");
  }
}

async function submitCheckin(e) {
  e.preventDefault();
  const dispId = document.getElementById('ci-dispatch-id').value;
  const condition = document.getElementById('ci-condition').value;
  const notes = document.getElementById('ci-damaged-notes').value;

  const res = await fetch('/api/checkin', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      dispatch_id: dispId,
      condition_in: condition,
      damaged_notes: notes
    })
  });

  if (res.ok) {
    closeModal('modal-checkin');
    await refreshAllData();
    alert("📦 Equipment return verified and restocked!");
  } else {
    alert("Failed to process return.");
  }
}


async function submitBrief(e) {
  e.preventDefault();
  const shootDate = document.getElementById('brf-date').value;
  const payload = {
    project_name: document.getElementById('brf-project').value,
    client: document.getElementById('brf-client').value,
    contact_person: document.getElementById('brf-contact-person')?.value || '',
    deliverables: document.getElementById('brf-deliverables')?.value || '',
    shoot_date: shootDate,
    shoot_end_date: document.getElementById('brf-end-date')?.value || shootDate,
    call_time: document.getElementById('brf-call').value,
    location: document.getElementById('brf-location').value,
    key_contacts: document.getElementById('brf-team')?.value || 'Saurabh Patil - Production Manager',
    cast_talent: document.getElementById('brf-team')?.value || '',
    status: document.getElementById('brf-status')?.value || 'Active',
    equipment_manifest: document.getElementById('brf-equipment')?.value || ''
  };

  const res = await fetch('/api/briefs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });

  if (res.ok) {
    closeModal('modal-brief');
    await refreshAllData();
    alert("🎯 Shoot successfully added to Shoot Tracker and Master Spreadsheet!");
  }
}

async function submitExpense(e) {
  e.preventDefault();
  const payload = {
    project_name: document.getElementById('exp-project').value,
    date: document.getElementById('exp-date').value,
    category: document.getElementById('exp-category').value,
    amount: parseFloat(document.getElementById('exp-amount').value),
    description: document.getElementById('exp-desc').value,
    paid_by: document.getElementById('exp-paid-by').value,
    mode: document.getElementById('exp-mode').value,
    receipt_image: document.getElementById('exp-receipt-url').value || null
  };

  const res = await fetch('/api/expenses', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });

  if (res.ok) {
    closeModal('modal-expense');
    await refreshAllData();
    alert("💰 Expense & Receipt logged successfully!");
  }
}

async function deleteExpense(expId) {
  if (!confirm(`Are you sure you want to remove expense ${expId}?`)) return;
  const res = await fetch(`/api/expenses/${expId}`, { method: 'DELETE' });
  if (res.ok) {
    await refreshAllData();
  }
}

async function deleteShoot(shootId) {
  if (!shootId) return;
  if (!confirm(`Are you sure you want to delete shoot ${shootId} from the Shoot Tracker?`)) {
    return;
  }
  try {
    let res = await fetch(`/api/briefs/${encodeURIComponent(shootId)}`, { method: 'DELETE' });
    if (!res.ok) {
      res = await fetch(`/api/briefs/delete/${encodeURIComponent(shootId)}`, { method: 'POST' });
    }
    if (res.ok) {
      await refreshAllData();
    } else {
      const err = await res.json().catch(() => ({}));
      alert(`Failed to delete shoot: ${err.detail || 'Server returned error'}`);
    }
  } catch (err) {
    console.error("Error deleting shoot:", err);
    alert("Network error. If you are running an existing server session, please close and restart launch_production_manager.bat.");
  }
}

// ----------------------------------------------------
// WhatsApp Message Generators
// ----------------------------------------------------
function buildWhatsAppMessage(b) {
  const mapsQuery = encodeURIComponent(b.location || '');
  const mapsLink = b.location ? `https://www.google.com/maps/search/?api=1&query=${mapsQuery}` : '';
  const equip = b.equipment_manifest || b.equipment_for_shoot || '';

  return [
    `🎬 *PRODUCTION CALL SHEET & SHOOT BRIEF*`,
    `━━━━━━━━━━━━━━━━━━━━`,
    `🎯 *Project:* ${b.project_name || 'Shoot'}`,
    `🏢 *Client:* ${b.client || 'Client'}`,
    b.contact_person ? `👤 *Client POC:* ${b.contact_person}` : '',
    `📦 *Deliverables:* ${b.deliverables || 'Shoot Coverage'}`,
    `📅 *Shoot Date:* ${b.shoot_date}`,
    `⏰ *Call / Reach Time:* ${b.call_time}`,
    `📍 *Location:* ${b.location}`,
    mapsLink ? `🗺️ *Google Maps:* ${mapsLink}` : '',
    b.cast_talent ? `👥 *Assigned Crew:* ${b.cast_talent}` : (b.key_contacts ? `👥 *Crew:* ${b.key_contacts}` : ''),
    equip ? `🎥 *Equipment for Shoot:* ${equip}` : '',
    `━━━━━━━━━━━━━━━━━━━━`,
    `📋 *Production Manager:* Saurabh Patil`,
    `⚠️ *Please report on time. Have a safe shoot!*`
  ].filter(Boolean).join('\n');
}

async function shareShootWhatsApp(shootId) {
  try {
    const res = await fetch('/api/briefs');
    if (!res.ok) return;
    const briefs = await res.json();
    const b = briefs.find(x => x.id === shootId);
    if (!b) return;

    const msg = buildWhatsAppMessage(b);
    try {
      await navigator.clipboard.writeText(msg);
    } catch (e) {}

    const waUrl = `https://api.whatsapp.com/send?text=${encodeURIComponent(msg)}`;
    window.open(waUrl, '_blank');
  } catch (err) {
    console.error("Error sharing on WhatsApp:", err);
  }
}

async function copyShootWhatsAppText(shootId) {
  try {
    const res = await fetch('/api/briefs');
    if (!res.ok) return;
    const briefs = await res.json();
    const b = briefs.find(x => x.id === shootId);
    if (!b) return;

    const msg = buildWhatsAppMessage(b);
    await navigator.clipboard.writeText(msg);
    alert("📋 WhatsApp Shoot Note copied to clipboard!\nYou can now open WhatsApp (Web or App) and press Ctrl+V to paste.");
  } catch (err) {
    console.error("Error copying shoot text:", err);
  }
}

async function openEditBriefModal(shootId) {
  try {
    const res = await fetch('/api/briefs');
    if (!res.ok) return;
    const briefs = await res.json();
    const b = briefs.find(x => x.id === shootId);
    if (!b) return;

    if (!b.is_editable) {
      alert(`🔒 Editing is locked for shoot ${b.id}.\nEdits are only accepted on the same day of creation (${b.created_date || b.created_at || b.shoot_date}).`);
      return;
    }

    document.getElementById('edit-brf-id').value = b.id;
    document.getElementById('edit-brf-project').value = b.project_name || '';
    document.getElementById('edit-brf-client').value = b.client || '';
    document.getElementById('edit-brf-contact-person').value = b.contact_person || '';
    document.getElementById('edit-brf-deliverables').value = b.deliverables || '';
    document.getElementById('edit-brf-date').value = b.shoot_date || '';
    document.getElementById('edit-brf-end-date').value = b.shoot_end_date || b.shoot_date || '';
    document.getElementById('edit-brf-call').value = b.call_time || '';
    document.getElementById('edit-brf-location').value = b.location || '';
    document.getElementById('edit-brf-team').value = b.cast_talent || b.key_contacts || '';
    document.getElementById('edit-brf-status').value = b.status || 'Active';
    document.getElementById('edit-brf-equipment').value = b.equipment_manifest || b.equipment_for_shoot || '';

    renderCrewChips('edit-brf-crew-chips', 'edit-brf-team');
    renderEquipmentChips('edit-brf-equipment-chips', 'edit-brf-equipment');
    openModal('modal-edit-brief');
  } catch (err) {
    console.error("Error opening edit modal:", err);
  }
}

async function submitEditBrief(e) {
  e.preventDefault();
  const shootId = document.getElementById('edit-brf-id').value;
  if (!shootId) return;

  const shootDate = document.getElementById('edit-brf-date').value;
  const payload = {
    project_name: document.getElementById('edit-brf-project').value,
    client: document.getElementById('edit-brf-client').value,
    contact_person: document.getElementById('edit-brf-contact-person').value,
    deliverables: document.getElementById('edit-brf-deliverables').value,
    shoot_date: shootDate,
    shoot_end_date: document.getElementById('edit-brf-end-date')?.value || shootDate,
    call_time: document.getElementById('edit-brf-call').value,
    location: document.getElementById('edit-brf-location').value,
    cast_talent: document.getElementById('edit-brf-team').value,
    key_contacts: document.getElementById('edit-brf-team').value,
    status: document.getElementById('edit-brf-status').value,
    equipment_manifest: document.getElementById('edit-brf-equipment')?.value || ''
  };

  try {
    let res = await fetch(`/api/briefs/${encodeURIComponent(shootId)}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      res = await fetch(`/api/briefs/update/${encodeURIComponent(shootId)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    }

    if (res.ok) {
      closeModal('modal-edit-brief');
      await refreshAllData();
      alert("✅ Shoot details updated successfully!");
    } else {
      const err = await res.json().catch(() => ({}));
      alert(`⚠️ Update rejected: ${err.detail || 'Editing window closed or server error'}`);
    }
  } catch (err) {
    console.error("Error updating shoot:", err);
    alert("Network error updating shoot details.");
  }
}

async function submitAddItem(e) {
  e.preventDefault();
  const payload = {
    id: document.getElementById('item-id').value,
    category: document.getElementById('item-category').value,
    name: document.getElementById('item-name').value,
    model: document.getElementById('item-model').value,
    serial: document.getElementById('item-serial').value,
    location: document.getElementById('item-location').value || 'Studio Vault',
    quantity: parseInt(document.getElementById('item-qty').value) || 1,
    status: 'Available',
    notes: document.getElementById('item-notes').value
  };

  const res = await fetch('/api/inventory', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });

  if (res.ok) {
    closeModal('modal-add-item');
    await refreshAllData();
    alert("🎥 Gear added to inventory and Excel sheet!");
  }
}

async function deleteItem(itemId) {
  if (!confirm(`Are you sure you want to remove item ${itemId} from inventory?`)) return;
  const res = await fetch(`/api/inventory/${itemId}`, { method: 'DELETE' });
  if (res.ok) {
    await refreshAllData();
  }
}

async function deleteDispatch(dispId) {
  if (!confirm(`Are you sure you want to delete equipment dispatch log ${dispId}?`)) return;
  try {
    let res = await fetch(`/api/dispatches/${encodeURIComponent(dispId)}`, { method: 'DELETE' });
    if (!res.ok) {
      res = await fetch(`/api/dispatches/delete/${encodeURIComponent(dispId)}`, { method: 'POST' });
    }
    if (res.ok) {
      await refreshAllData();
      alert(`🗑️ Dispatch log ${dispId} deleted successfully!`);
    } else {
      alert("Failed to delete dispatch log.");
    }
  } catch (e) {
    console.error("Error deleting dispatch:", e);
    alert("Error deleting dispatch log.");
  }
}

async function deleteShoot(shootId) {
  if (!confirm(`Are you sure you want to delete shoot ${shootId}?`)) return;
  try {
    let res = await fetch(`/api/briefs/${encodeURIComponent(shootId)}`, { method: 'DELETE' });
    if (!res.ok) {
      res = await fetch(`/api/briefs/delete/${encodeURIComponent(shootId)}`, { method: 'POST' });
    }
    if (res.ok) {
      await refreshAllData();
      alert(`🗑️ Shoot ${shootId} deleted successfully!`);
    } else {
      alert("Failed to delete shoot.");
    }
  } catch (e) {
    console.error("Error deleting shoot:", e);
    alert("Error deleting shoot.");
  }
}

async function deleteExpense(expId) {
  if (!confirm(`Are you sure you want to delete expense ${expId}?`)) return;
  try {
    let res = await fetch(`/api/expenses/${encodeURIComponent(expId)}`, { method: 'DELETE' });
    if (!res.ok) {
      res = await fetch(`/api/expenses/delete/${encodeURIComponent(expId)}`, { method: 'POST' });
    }
    if (res.ok) {
      await refreshAllData();
      alert(`🗑️ Expense ${expId} deleted successfully!`);
    } else {
      alert("Failed to delete expense.");
    }
  } catch (e) {
    console.error("Error deleting expense:", e);
    alert("Error deleting expense.");
  }
}

async function submitImport(e) {
  e.preventDefault();
  const csvText = document.getElementById('import-csv-text').value;
  const mode = document.querySelector('input[name="import-mode"]:checked').value;

  if (!csvText.trim()) {
    alert("Please paste CSV data to import.");
    return;
  }

  const res = await fetch('/api/inventory/import', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      csv_text: csvText,
      append: mode === 'append'
    })
  });

  if (res.ok) {
    const data = await res.json();
    closeModal('modal-import');
    await refreshAllData();
    alert(`🎉 Successfully imported ${data.count} equipment items! Master Spreadsheet updated.`);
  } else {
    alert("Failed to import CSV data. Please check header format.");
  }
}

// ----------------------------------------------------
// AI Chat Assistant
// ----------------------------------------------------
function sendQuickPrompt(text) {
  switchTab('ai-assistant');
  const input = document.getElementById('ai-chat-input');
  input.value = text;
  document.getElementById('ai-chat-form').dispatchEvent(new Event('submit'));
}

async function handleChatSubmit(e) {
  e.preventDefault();
  const input = document.getElementById('ai-chat-input');
  const prompt = input.value.trim();
  if (!prompt) return;

  const history = document.getElementById('ai-chat-history');
  
  // Append user bubble
  const userBubble = document.createElement('div');
  userBubble.className = 'chat-bubble chat-user';
  userBubble.textContent = prompt;
  history.appendChild(userBubble);
  input.value = '';
  history.scrollTop = history.scrollHeight;

  // Append typing indicator
  const botBubble = document.createElement('div');
  botBubble.className = 'chat-bubble chat-agent';
  botBubble.innerHTML = '<em>Processing command via Saurabh Patil Desk...</em>';
  history.appendChild(botBubble);
  history.scrollTop = history.scrollHeight;

  try {
    const res = await fetch('/api/ai/command', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt: prompt, session_id: 'user_session' })
    });

    const data = await res.json();
    let formattedMsg = (data.message || 'Done')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" style="color: #38bdf8; text-decoration: underline; font-weight: 600;">$1</a>')
      .replace(/`(.*?)`/g, '<code style="background: rgba(0,0,0,0.4); padding: 2px 6px; border-radius: 4px; color: #38bdf8;">$1</code>')
      .replace(/\n/g, '<br>');

    botBubble.innerHTML = formattedMsg;
    await refreshAllData();
  } catch (err) {
    botBubble.innerHTML = '❌ An error occurred while executing the production command.';
  }

  history.scrollTop = history.scrollHeight;
}

// ----------------------------------------------------
// Live Studio Timecode Clock (24 FPS Precision SMPTE)
// ----------------------------------------------------
function startStudioTimecode() {
  const el = document.getElementById('live-studio-timecode');
  if (!el) return;

  function update() {
    const now = new Date();
    const hrs = String(now.getHours()).padStart(2, '0');
    const mins = String(now.getMinutes()).padStart(2, '0');
    const secs = String(now.getSeconds()).padStart(2, '0');
    const ms = now.getMilliseconds();
    const frame = String(Math.floor((ms / 1000) * 24)).padStart(2, '0');
    el.textContent = `${hrs}:${mins}:${secs}:${frame}`;
    requestAnimationFrame(update);
  }
  requestAnimationFrame(update);
}

// ----------------------------------------------------
// App Initialization
// ----------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  startStudioTimecode();
  refreshAllData();
  const chatForm = document.getElementById('ai-chat-form');
  if (chatForm) {
    chatForm.addEventListener('submit', handleChatSubmit);
  }
  // Live On-Set Tracker: auto-refresh every 10 seconds
  setInterval(() => {
    try { refreshDesktopLiveTracker(); } catch (e) { /* silent */ }
  }, 10000);
});

// Immediate execution if script is loaded after DOM ready
if (document.readyState === 'complete' || document.readyState === 'interactive') {
  initTabs();
  startStudioTimecode();
  refreshAllData();
}
