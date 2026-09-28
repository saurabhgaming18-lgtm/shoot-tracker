/**
 * Mobile Shoot Tracker - Frontend Core Application
 * Focus: Today Tab, Verification (Clapperboard Shot Logger), and Gear Verification.
 */

(function () {
  'use strict';

  // State
  let currentUser = null;
  let authToken = localStorage.getItem('pos_mobile_token') || null;
  let activeShootId = null;
  let shootsList = [];
  let currentShootData = null;

  // Clapperboard state
  let clapperState = {
    scene: 1,
    shot: 1,
    take: 1,
    isGood: true,
    cameraRoll: 'A001',
    soundRoll: 'S001'
  };

  // DOM Elements Cache
  const authModal = document.getElementById('auth-modal');
  const loginForm = document.getElementById('login-form');
  const loginUserInput = document.getElementById('login-username');
  const loginPassInput = document.getElementById('login-password');
  const userDisplayName = document.getElementById('user-display-name');
  const headerCrewRole = document.getElementById('header-crew-role');
  const btnUserProfile = document.getElementById('btn-user-profile');
  const activeShootSelect = document.getElementById('active-shoot-select');
  const btnRefreshData = document.getElementById('btn-refresh-data');
  const btnShareQr = document.getElementById('btn-share-qr');
  const qrModal = document.getElementById('qr-modal');
  const btnCloseQr = document.getElementById('btn-close-qr');
  const btnCopyUrl = document.getElementById('btn-copy-url');

  // Navigation Items (3 Tabs: Today, Verification, Gear Verification)
  const navItems = document.querySelectorAll('.bottom-nav .nav-item');
  const tabScreens = document.querySelectorAll('.tab-screen');

  // Hero Card Elements (Tab 1: Today)
  const heroShootTitle = document.getElementById('hero-shoot-title');
  const heroShootStatus = document.getElementById('hero-shoot-status');
  const heroShootDate = document.getElementById('hero-shoot-date');
  const heroCallTime = document.getElementById('hero-call-time');
  const heroClient = document.getElementById('hero-client');
  const heroLocation = document.getElementById('hero-location');
  const heroCrew = document.getElementById('hero-crew');
  const btnOpenMaps = document.getElementById('btn-open-maps');
  const btnCallContact = document.getElementById('btn-call-contact');

  // Clapper Elements (Tab 2: Verification)
  const dispScene = document.getElementById('disp-scene');
  const dispShot = document.getElementById('disp-shot');
  const dispTake = document.getElementById('disp-take');
  const btnSceneMinus = document.getElementById('btn-scene-minus');
  const btnScenePlus = document.getElementById('btn-scene-plus');
  const btnShotMinus = document.getElementById('btn-shot-minus');
  const btnShotPlus = document.getElementById('btn-shot-plus');
  const btnTakeMinus = document.getElementById('btn-take-minus');
  const btnTakePlus = document.getElementById('btn-take-plus');
  const toggleGoodTake = document.getElementById('toggle-good-take');
  const toggleNgTake = document.getElementById('toggle-ng-take');
  const inputShotNotes = document.getElementById('input-shot-notes');
  const inputCameraRoll = document.getElementById('input-camera-roll');
  const inputSoundRoll = document.getElementById('input-sound-roll');
  const btnSubmitTake = document.getElementById('btn-submit-take');
  const shotsHistoryList = document.getElementById('shots-history-list');
  const shotsTotalCount = document.getElementById('shots-total-count');

  // Gear Elements (Tab 3: Gear Verification)
  const gearChecklistContainer = document.getElementById('gear-checklist-container');
  const gearCountBadge = document.getElementById('gear-count-badge');

  // Activity Feed Element
  const activityFeedList = document.getElementById('activity-feed-list');

  // ----------------------------------------------------
  // Helper: Toast Notifications
  // ----------------------------------------------------
  function showToast(message, icon = '✅') {
    const existing = document.querySelector('.toast-msg');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = 'toast-msg';
    toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
    document.body.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transition = 'opacity 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 2400);
  }

  // ----------------------------------------------------
  // Authentication Handlers (Standard Clean Login)
  // ----------------------------------------------------
  async function checkAuthSession() {
    if (!authToken) {
      showAuthModal();
      return;
    }

    try {
      const res = await fetch('/api/auth/me', {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      if (res.ok) {
        const data = await res.json();
        currentUser = data.user;
        renderUserProfile();
        hideAuthModal();
        loadActiveShoots();
      } else {
        localStorage.removeItem('pos_mobile_token');
        authToken = null;
        showAuthModal();
      }
    } catch (err) {
      console.warn('Network issue checking session:', err);
      const cached = localStorage.getItem('pos_cached_user');
      if (cached) {
        currentUser = JSON.parse(cached);
        renderUserProfile();
        hideAuthModal();
        loadActiveShoots();
      } else {
        showAuthModal();
      }
    }
  }

  function showAuthModal() {
    authModal.classList.remove('hidden');
  }

  function hideAuthModal() {
    authModal.classList.add('hidden');
  }

  function renderUserProfile() {
    if (currentUser) {
      userDisplayName.textContent = currentUser.name.split(' ')[0] || 'Crew';
      headerCrewRole.textContent = currentUser.role || 'Crew Member';
    }
  }

  loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = loginUserInput.value.trim();
    const password = loginPassInput.value.trim();

    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });

      const data = await res.json();
      if (res.ok && data.session) {
        authToken = data.session.token;
        currentUser = data.session;
        localStorage.setItem('pos_mobile_token', authToken);
        localStorage.setItem('pos_cached_user', JSON.stringify(currentUser));
        renderUserProfile();
        hideAuthModal();
        showToast(`Welcome, ${currentUser.name}!`, '🎬');
        loadActiveShoots();
      } else {
        showToast(data.detail || 'Invalid username or password.', '⚠️');
      }
    } catch (err) {
      showToast('Connection error. Please try again.', '❌');
    }
  });

  btnUserProfile.addEventListener('click', () => {
    if (!currentUser) return;
    const confirmLogout = confirm(`Logged in as: ${currentUser.name} (${currentUser.role})\n\nDo you want to log out?`);
    if (confirmLogout) {
      fetch('/api/auth/logout', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${authToken}` }
      }).finally(() => {
        localStorage.removeItem('pos_mobile_token');
        localStorage.removeItem('pos_cached_user');
        authToken = null;
        currentUser = null;
        showAuthModal();
      });
    }
  });

  // ----------------------------------------------------
  // Bottom Navigation Switching (3 Tabs)
  // ----------------------------------------------------
  navItems.forEach(item => {
    item.addEventListener('click', () => {
      navItems.forEach(n => n.classList.remove('active'));
      tabScreens.forEach(t => t.classList.remove('active'));

      item.classList.add('active');
      const targetId = item.dataset.tab;
      const targetTab = document.getElementById(targetId);
      if (targetTab) {
        targetTab.classList.add('active');
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }
    });
  });

  // ----------------------------------------------------
  // Load Active Shoots
  // ----------------------------------------------------
  async function loadActiveShoots() {
    try {
      const res = await fetch('/api/tracker/shoots');
      if (res.ok) {
        shootsList = await res.json();
        renderShootDropdown();
        if (shootsList.length > 0) {
          const savedShootId = localStorage.getItem('pos_active_shoot_id');
          if (savedShootId && shootsList.some(s => s.id === savedShootId)) {
            activeShootId = savedShootId;
          } else {
            activeShootId = shootsList[0].id;
          }
          activeShootSelect.value = activeShootId;
          loadShootDetails(activeShootId);
        } else {
          heroShootTitle.textContent = 'No Shoots Scheduled';
        }
      }
    } catch (err) {
      console.warn('Error loading shoots list:', err);
    }
  }

  function renderShootDropdown() {
    activeShootSelect.innerHTML = '';
    if (shootsList.length === 0) {
      activeShootSelect.innerHTML = '<option value="">No Active Shoots Found</option>';
      return;
    }

    shootsList.forEach(shoot => {
      const opt = document.createElement('option');
      opt.value = shoot.id;
      opt.textContent = `${shoot.project_name} (${shoot.shoot_date || 'Date TBD'}) - ${shoot.client || 'Client'}`;
      activeShootSelect.appendChild(opt);
    });
  }

  activeShootSelect.addEventListener('change', (e) => {
    activeShootId = e.target.value;
    localStorage.setItem('pos_active_shoot_id', activeShootId);
    loadShootDetails(activeShootId);
  });

  btnRefreshData.addEventListener('click', () => {
    btnRefreshData.style.transform = 'rotate(360deg)';
    btnRefreshData.style.transition = 'transform 0.4s ease';
    setTimeout(() => { btnRefreshData.style.transform = 'none'; }, 400);
    if (activeShootId) {
      loadShootDetails(activeShootId);
    } else {
      loadActiveShoots();
    }
  });

  // ----------------------------------------------------
  // Load Shoot Details & Render
  // ----------------------------------------------------
  async function loadShootDetails(shootId) {
    if (!shootId) return;

    try {
      const res = await fetch(`/api/tracker/shoot/${shootId}`);
      if (res.ok) {
        currentShootData = await res.json();
        renderDashboard(currentShootData);
        renderShotsList(currentShootData.shots || []);
        renderGearChecklist(currentShootData.gear_checklist || []);
        renderActivityFeed(currentShootData.activity || []);
      } else if (res.status === 404) {
        // Shoot was deleted or no longer exists — clear stale cached ID and reload
        console.warn(`Shoot ${shootId} not found (deleted?). Reloading shoots list...`);
        localStorage.removeItem('pos_active_shoot_id');
        activeShootId = null;
        currentShootData = null;
        // Reload the list — will auto-pick the first valid shoot
        await loadActiveShoots();
      } else {
        console.warn('Server error fetching shoot:', res.status);
      }
    } catch (err) {
      console.warn('Network error fetching shoot detail:', err);
    }
  }

  // ----------------------------------------------------
  // 1. Tab 1: Today Dashboard & Call Sheet
  // ----------------------------------------------------
  function renderDashboard(data) {
    const b = data.brief || {};
    heroShootTitle.textContent = b.project_name || 'Production Shoot';
    heroShootStatus.textContent = b.status || 'Active';
    heroShootDate.textContent = b.shoot_date || '--';
    heroCallTime.textContent = b.call_time || '--';
    heroClient.textContent = `${b.client || ''} ${b.contact_person ? '(' + b.contact_person + ')' : ''}` || '--';
    heroLocation.textContent = b.location || 'Studio Location';
    heroCrew.textContent = b.key_contacts || b.cast_talent || 'Production Crew';

    // Google Maps Link
    if (b.location && b.location.includes('http')) {
      const urlMatch = b.location.match(/(https?:\/\/[^\s]+)/);
      btnOpenMaps.href = urlMatch ? urlMatch[0] : `https://maps.google.com/?q=${encodeURIComponent(b.location)}`;
    } else {
      btnOpenMaps.href = `https://maps.google.com/?q=${encodeURIComponent(b.location || 'Studio')}`;
    }

    // Call Client link
    if (b.contact_person) {
      const numMatch = b.contact_person.match(/(\+?[0-9\s-]{10,14})/);
      if (numMatch) {
        btnCallContact.href = `tel:${numMatch[0].replace(/[\s-]/g, '')}`;
        btnCallContact.style.display = 'flex';
      } else {
        btnCallContact.style.display = 'none';
      }
    } else {
      btnCallContact.style.display = 'none';
    }

    // Milestones Status
    const milestones = data.milestones || [];
    const milestoneTypes = milestones.map(m => m.type);

    document.querySelectorAll('.milestone-btn').forEach(btn => {
      const type = btn.dataset.milestone;
      const timeSpan = btn.querySelector('.milestone-time');
      const found = milestones.find(m => m.type === type);

      if (found) {
        btn.classList.add('checked');
        if (timeSpan) {
          timeSpan.textContent = found.time_str;
          timeSpan.style.display = 'block';
        }
      } else {
        btn.classList.remove('checked');
        if (timeSpan) {
          timeSpan.textContent = '';
          timeSpan.style.display = 'none';
        }
      }
    });
  }

  // Milestone Click
  document.querySelectorAll('.milestone-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      if (!activeShootId) {
        showToast('Please select an active shoot first', '⚠️');
        return;
      }

      const mType = btn.dataset.milestone;
      const label = btn.querySelector('.milestone-label')?.textContent || btn.textContent.trim();
      const crewName = currentUser ? currentUser.name : 'Crew Member';

      try {
        const res = await fetch('/api/tracker/milestones', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            shoot_id: activeShootId,
            milestone_type: mType,
            crew_name: crewName,
            notes: ''
          })
        });

        if (res.ok) {
          btn.classList.add('checked');
          showToast(`Logged: ${label}`, '⚡');
          loadShootDetails(activeShootId);
        }
      } catch (err) {
        showToast('Error logging milestone', '❌');
      }
    });
  });

  // ----------------------------------------------------
  // 2. Tab 2: Verification (Clapperboard Shot / Take Logger)
  // ----------------------------------------------------
  function updateClapperDisplay() {
    dispScene.textContent = clapperState.scene;
    dispShot.textContent = clapperState.shot;
    dispTake.textContent = clapperState.take;

    if (clapperState.isGood) {
      toggleGoodTake.classList.add('selected');
      toggleNgTake.classList.remove('selected');
    } else {
      toggleGoodTake.classList.remove('selected');
      toggleNgTake.classList.add('selected');
    }
  }

  btnSceneMinus.addEventListener('click', () => { if (clapperState.scene > 1) { clapperState.scene--; updateClapperDisplay(); } });
  btnScenePlus.addEventListener('click', () => { clapperState.scene++; updateClapperDisplay(); });

  btnShotMinus.addEventListener('click', () => { if (clapperState.shot > 1) { clapperState.shot--; updateClapperDisplay(); } });
  btnShotPlus.addEventListener('click', () => { clapperState.shot++; updateClapperDisplay(); });

  btnTakeMinus.addEventListener('click', () => { if (clapperState.take > 1) { clapperState.take--; updateClapperDisplay(); } });
  btnTakePlus.addEventListener('click', () => { clapperState.take++; updateClapperDisplay(); });

  toggleGoodTake.addEventListener('click', () => { clapperState.isGood = true; updateClapperDisplay(); });
  toggleNgTake.addEventListener('click', () => { clapperState.isGood = false; updateClapperDisplay(); });

  btnSubmitTake.addEventListener('click', async () => {
    if (!activeShootId) {
      showToast('Select an active shoot first', '⚠️');
      return;
    }

    const payload = {
      shoot_id: activeShootId,
      scene: String(clapperState.scene),
      shot: String(clapperState.shot),
      take: clapperState.take,
      is_circle: clapperState.isGood,
      status: clapperState.isGood ? 'Good' : 'NG',
      notes: inputShotNotes.value.trim(),
      crew_name: currentUser ? currentUser.name : 'Camera Dept',
      camera_roll: inputCameraRoll.value.trim() || 'A001',
      sound_roll: inputSoundRoll.value.trim() || 'S001'
    };

    try {
      const res = await fetch('/api/tracker/shots', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        showToast(`Scene ${payload.scene} Take ${payload.take} Verified!`, clapperState.isGood ? '⭐' : '🎬');
        inputShotNotes.value = '';
        clapperState.take++;
        updateClapperDisplay();
        loadShootDetails(activeShootId);
      }
    } catch (err) {
      showToast('Error saving take', '❌');
    }
  });

  function renderShotsList(shots) {
    shotsTotalCount.textContent = shots.length;
    shotsHistoryList.innerHTML = '';

    if (shots.length === 0) {
      shotsHistoryList.innerHTML = `
        <div style="text-align: center; color: var(--text-muted); padding: 16px; font-size: 12px;">
          No takes logged for this shoot yet. Tap "Log Take & Verify" above!
        </div>`;
      return;
    }

    const reversed = [...shots].reverse();
    reversed.forEach(s => {
      const item = document.createElement('div');
      item.className = 'shot-log-item';

      const isGood = s.is_circle || s.status === 'Good';
      const starIcon = isGood ? '⭐' : '⚪';

      item.innerHTML = `
        <div class="shot-info-left">
          <div class="shot-scene-tag">
            <span style="color:var(--color-gold);">SCENE ${s.scene}</span> • SHOT ${s.shot} • TAKE ${s.take}
            <span class="badge ${isGood ? 'badge-active' : 'badge-gold'}" style="margin-left: 6px; font-size: 9px;">${s.status || (isGood ? 'Good' : 'NG')}</span>
          </div>
          <div class="shot-notes">${s.notes ? s.notes : '<i style="color:var(--text-muted)">No notes</i>'}</div>
          <div class="shot-time-crew">🕒 ${s.time_str || ''} by ${s.crew_name || 'Crew'} • Cam: ${s.camera_roll || 'A001'}</div>
        </div>
        <div style="display: flex; align-items: center; gap: 8px;">
          <span class="shot-circle-star" title="Toggle Circle Take">${starIcon}</span>
          <button class="header-user-btn btn-delete-shot" style="padding: 4px 8px; color: var(--color-red); font-size: 11px;">✕</button>
        </div>
      `;

      item.querySelector('.shot-circle-star').addEventListener('click', async () => {
        try {
          const res = await fetch(`/api/tracker/shots/${s.id}/circle`, { method: 'POST' });
          if (res.ok) {
            loadShootDetails(activeShootId);
          }
        } catch (e) {
          console.error(e);
        }
      });

      item.querySelector('.btn-delete-shot').addEventListener('click', async () => {
        if (confirm(`Delete Scene ${s.scene} Shot ${s.shot} Take ${s.take}?`)) {
          try {
            const res = await fetch(`/api/tracker/shots/${s.id}`, { method: 'DELETE' });
            if (res.ok) {
              showToast('Take deleted', '🗑️');
              loadShootDetails(activeShootId);
            }
          } catch (e) {
            console.error(e);
          }
        }
      });

      shotsHistoryList.appendChild(item);
    });
  }

  // ----------------------------------------------------
  // 3. Tab 3: Gear Verification
  // ----------------------------------------------------
  function renderGearChecklist(gearItems) {
    gearCountBadge.textContent = `${gearItems.length} Items`;
    gearChecklistContainer.innerHTML = '';

    if (gearItems.length === 0) {
      gearChecklistContainer.innerHTML = `
        <div style="text-align: center; color: var(--text-muted); padding: 16px; font-size: 12px;">
          No equipment manifest found in shoot brief.
        </div>`;
      return;
    }

    gearItems.forEach(item => {
      const card = document.createElement('div');
      card.className = 'gear-check-item';

      card.innerHTML = `
        <div class="gear-name-row">
          <span>📹 ${item.name}</span>
          ${item.damaged ? '<span class="badge" style="background:rgba(239,68,68,0.2); color:#f87171;">⚠️ Issue</span>' : ''}
        </div>
        <div class="gear-actions-row">
          <button class="btn-gear-step ${item.packed ? 'active' : ''}" data-action="packed">
            ${item.packed ? '✓' : '○'} Packed
          </button>
          <button class="btn-gear-step ${item.on_set ? 'active' : ''}" data-action="on_set">
            ${item.on_set ? '✓' : '○'} On Set
          </button>
          <button class="btn-gear-step ${item.returned ? 'active' : ''}" data-action="returned">
            ${item.returned ? '✓' : '○'} Returned
          </button>
          <button class="btn-gear-step danger ${item.damaged ? 'active' : ''}" data-action="damaged">
            ⚠️ Flag
          </button>
        </div>
      `;

      card.querySelectorAll('.btn-gear-step').forEach(btn => {
        btn.addEventListener('click', async () => {
          const action = btn.dataset.action;
          const patchData = { item_key: item.key, name: item.name, crew_name: currentUser ? currentUser.name : 'Crew' };

          if (action === 'packed') patchData.packed = !item.packed;
          if (action === 'on_set') patchData.on_set = !item.on_set;
          if (action === 'returned') patchData.returned = !item.returned;
          if (action === 'damaged') {
            const isDamaged = !item.damaged;
            patchData.damaged = isDamaged;
            if (isDamaged) {
              const reason = prompt(`Enter damage/issue notes for ${item.name}:`);
              patchData.damage_notes = reason || 'Flagged on set';
            }
          }

          try {
            const res = await fetch(`/api/tracker/equipment/${activeShootId}`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(patchData)
            });
            if (res.ok) {
              loadShootDetails(activeShootId);
            }
          } catch (e) {
            console.error(e);
          }
        });
      });

      gearChecklistContainer.appendChild(card);
    });
  }

  // ----------------------------------------------------
  // Activity Feed (Tab 1)
  // ----------------------------------------------------
  function renderActivityFeed(activities) {
    activityFeedList.innerHTML = '';
    if (activities.length === 0) {
      activityFeedList.innerHTML = `
        <div style="text-align: center; color: var(--text-muted); padding: 12px; font-size: 12px;">
          No live activities yet today.
        </div>`;
      return;
    }

    activities.forEach(act => {
      const row = document.createElement('div');
      row.className = 'activity-item';

      const initial = (act.crew_name || 'C').charAt(0).toUpperCase();
      const color = act.category === 'shot' ? '#f59e0b' : act.category === 'milestone' ? '#10b981' : '#3b82f6';

      row.innerHTML = `
        <div class="activity-avatar" style="background: ${color};">${initial}</div>
        <div class="activity-details">
          <div class="activity-action">${act.action}</div>
          <div class="activity-desc">${act.details || ''} • by ${act.crew_name}</div>
        </div>
        <div class="activity-time">${act.time_str || ''}</div>
      `;
      activityFeedList.appendChild(row);
    });
  }

  // ----------------------------------------------------
  // QR Code / Phone Connect
  // ----------------------------------------------------
  btnShareQr.addEventListener('click', async () => {
    try {
      let mobileUrl = window.location.origin + '/mobile';
      if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        const res = await fetch('/api/network_info');
        const data = await res.json();
        if (data.mobile_url) {
          mobileUrl = data.mobile_url;
        }
      }

      document.getElementById('network-mobile-url').textContent = mobileUrl;
      const qrApiUrl = `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(mobileUrl)}`;
      document.getElementById('qr-image').src = qrApiUrl;
      qrModal.classList.remove('hidden');
    } catch (e) {
      qrModal.classList.remove('hidden');
    }
  });

  btnCloseQr.addEventListener('click', () => {
    qrModal.classList.add('hidden');
  });

  btnCopyUrl.addEventListener('click', () => {
    const urlText = document.getElementById('network-mobile-url').textContent.trim();
    if (navigator.clipboard) {
      navigator.clipboard.writeText(urlText);
      showToast('Link copied to clipboard!', '📋');
    } else {
      showToast(urlText, '🔗');
    }
  });

  // Background Auto-Sync every 15 seconds
  setInterval(() => {
    if (activeShootId && authToken) {
      loadShootDetails(activeShootId);
    }
  }, 15000);

  // Initialize App
  checkAuthSession();

})();
