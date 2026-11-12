/**
 * VitaSteps Kitérő — PWA Alkalmazás
 * Tactical Carto Navigáció, Leaflet Térkép, Geofencing, Audio/TTS, Gestalt Gyűrű & Teszt Szimulátor
 */

(function () {
  'use strict';

  // ══════════════════════════════════════════════════════════════
  // 1. ÁLLAPOT & VÁLTOZÓK
  // ══════════════════════════════════════════════════════════════
  const STORAGE_KEY = 'kitero_progress_m1';
  const THEME_KEY = 'kitero_theme';
  const GEOFENCE_RADIUS_METERS = 35;

  let tourData = null;
  let activeStopIndex = 0;
  let completedStopIds = new Set();
  let startTime = null;
  let isFinished = false;

  // Felhasználói GPS Pozíció
  let userCoords = null; // [lat, lng]
  let userAccuracy = 0;
  let isSimulatedGPS = false;
  let geoWatchId = null;

  // Leaflet Térkép
  let map = null;
  let stopMarkers = [];
  let userMarker = null;
  let accuracyCircle = null;
  let routePolyline = null;
  let completedPolyline = null;
  let tileLayer = null;

  // Wake Lock API
  let wakeLockSentinel = null;

  // Audio Lejátszó & Valódi Piper MP3 / WAV
  let audioMode = 'hook'; // 'hook' | 'story'
  let isAudioPlaying = false;
  let playbackRate = 1.0;
  let audioTimer = null;
  let audioElapsedSec = 0;
  let audioTotalSec = 150;
  let activeUtterance = null;
  let nativeAudio = new Audio(); // HTML5 Audio elem a Piper fájlokhoz

  // ══════════════════════════════════════════════════════════════
  // 2. INICIALIZÁLÁS
  // ══════════════════════════════════════════════════════════════
  document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    loadTourData();
    setupNavigation();
    setupTestMode();
    setupWakeLock();
    setupAudioDeck();
    setupDiplomaActions();
  });

  // Téma betöltése és váltása
  function initTheme() {
    const savedTheme = localStorage.getItem(THEME_KEY) || 'light';
    setTheme(savedTheme);

    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    if (themeToggleBtn) {
      themeToggleBtn.addEventListener('click', () => {
        const currentTheme = document.body.classList.contains('theme-dark') ? 'dark' : 'light';
        const nextTheme = currentTheme === 'light' ? 'dark' : 'light';
        setTheme(nextTheme);
      });
    }
  }

  function setTheme(theme) {
    document.body.className = 'theme-' + theme;
    localStorage.setItem(THEME_KEY, theme);

    const icon = document.getElementById('theme-icon');
    if (icon) {
      icon.textContent = theme === 'light' ? 'dark_mode' : 'light_mode';
    }

    if (map && tileLayer) {
      updateMapTileTheme(theme);
    }
  }

  function updateMapTileTheme(theme) {
    if (!map) return;
    
    // Hosszúlépésben bevált és stabil CartoDB dark csempe:
    const tileUrl = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';

    if (tileLayer) {
      map.removeLayer(tileLayer);
    }
    tileLayer = L.tileLayer(tileUrl, {
      maxZoom: 19,
      subdomains: 'abcd',
      attribution: '&copy; OpenStreetMap contributors &copy; CARTO'
    }).addTo(map);
  }

  // ══════════════════════════════════════════════════════════════
  // 3. TÚRA ADATOK BETÖLTÉSE ÉS ÁLLAPOT VISSZAÁLLÍTÁSA
  // ══════════════════════════════════════════════════════════════
  async function loadTourData() {
    try {
      const res = await fetch('./tour_m1.json');
      if (!res.ok) throw new Error('Nem sikerült betölteni a tour_m1.json fájlt');
      tourData = await res.json();

      loadSavedProgress();
      renderBriefScreen();
      initMap();
      updateGestaltRing();
      updateHUD();
      updateStoryScreen();
      renderVaultList();
      updateProfileScreen();

      // GPS figyelés indítása
      startGeolocationTracking();

      // URL ellenőrzés test_mode-ra
      const params = new URLSearchParams(window.location.search);
      if (params.get('test_mode') === '1') {
        openTestPanel();
      }
    } catch (err) {
      console.error('Hiba a túraadatok betöltésekor:', err);
      showToast('Hiba a túraadatok betöltésekor', 'error');
    }
  }

  function loadSavedProgress() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const data = JSON.parse(raw);
        if (Array.isArray(data.completedStopIds)) {
          completedStopIds = new Set(data.completedStopIds);
        }
        if (typeof data.activeStopIndex === 'number') {
          activeStopIndex = Math.min(data.activeStopIndex, (tourData?.pois?.length || 9) - 1);
        }
        if (data.startTime) {
          startTime = new Date(data.startTime);
        }
        if (data.isFinished) {
          isFinished = true;
        }
      }
    } catch (e) {
      console.warn('Nem sikerült a korábbi haladást visszaállítani', e);
    }

    if (!startTime) {
      startTime = new Date();
    }
  }

  function saveProgress() {
    const payload = {
      completedStopIds: Array.from(completedStopIds),
      activeStopIndex,
      startTime: startTime ? startTime.toISOString() : null,
      isFinished
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
  }

  // ══════════════════════════════════════════════════════════════
  // 4. KÉPERNYŐ NAVIGÁCIÓ & GESTALT GYŰRŰ
  // ══════════════════════════════════════════════════════════════
  function setupNavigation() {
    // Alsó fülek
    const navButtons = document.querySelectorAll('.bottom-nav-bar .nav-tab-btn');
    navButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        const targetScreen = btn.getAttribute('data-screen');
        if (targetScreen) showScreen(targetScreen);
      });
    });

    // Indítás CTA
    const btnStartWalk = document.getElementById('btn-start-walk');
    if (btnStartWalk) {
      btnStartWalk.addEventListener('click', () => {
        showScreen('screen-map');
        requestWakeLock();
        showToast('Séta elindítva! Keresd a következő állomást a térképen.');
      });
    }

    // Gestalt widget kattintás
    const gestaltWidget = document.getElementById('gestalt-progress-widget');
    if (gestaltWidget) {
      gestaltWidget.addEventListener('click', () => {
        if (isFinished || completedStopIds.size === tourData?.pois?.length) {
          showScreen('screen-finish');
        } else {
          showScreen('screen-brief');
        }
      });
    }

    // Vissza a térképhez a történetből
    const btnBackToMap = document.getElementById('btn-back-to-map');
    if (btnBackToMap) {
      btnBackToMap.addEventListener('click', () => showScreen('screen-map'));
    }

    // Profil megnyitása oklevélből
    const btnProfileFromFinish = document.getElementById('btn-view-profile-from-finish');
    if (btnProfileFromFinish) {
      btnProfileFromFinish.addEventListener('click', () => showScreen('screen-profile'));
    }
  }

  function showScreen(screenId) {
    document.querySelectorAll('.screen-pane').forEach(p => p.classList.remove('active'));
    const target = document.getElementById(screenId);
    if (target) {
      target.classList.add('active');
    }

    // Alsó fül aktív jelölése
    const navButtons = document.querySelectorAll('.bottom-nav-bar .nav-tab-btn');
    navButtons.forEach(btn => {
      btn.classList.toggle('active', btn.getAttribute('data-screen') === screenId);
    });

    // Ha térkép, méret újraszámolása
    if (screenId === 'screen-map' && map) {
      setTimeout(() => {
        map.invalidateSize();
        centerMapOnActive();
      }, 150);
    }
  }

  function updateGestaltRing() {
    if (!tourData || !tourData.pois) return;
    const total = tourData.pois.length;
    const completed = completedStopIds.size;

    const ringCircle = document.getElementById('gestalt-circle');
    const ringText = document.getElementById('gestalt-text');

    if (ringCircle) {
      const circumference = 44; // 2 * PI * 7
      const offset = circumference - (completed / total) * circumference;
      ringCircle.style.strokeDashoffset = offset;
    }

    if (ringText) {
      ringText.textContent = `${completed} / ${total} Megálló`;
    }

    const briefSummary = document.getElementById('brief-progress-summary');
    if (briefSummary) {
      briefSummary.textContent = `${completed} / ${total} kész`;
    }
  }

  // ══════════════════════════════════════════════════════════════
  // 5. SCREEN 1: BRIEF NÉZET RENDERELÉSE
  // ══════════════════════════════════════════════════════════════
  function renderBriefScreen() {
    if (!tourData) return;

    const titleEl = document.getElementById('brief-title');
    const subEl = document.getElementById('brief-subtitle');
    const headerTitle = document.getElementById('header-tour-title');
    const secretsCount = document.getElementById('brief-secrets-count');

    if (titleEl) titleEl.textContent = tourData.title;
    if (subEl) subEl.textContent = tourData.subtitle;
    if (headerTitle) headerTitle.textContent = 'Kisföldalatti';
    if (secretsCount) secretsCount.textContent = `${tourData.pois.length} Titok`;

    const container = document.getElementById('brief-stops-container');
    if (!container) return;

    container.innerHTML = '';
    tourData.pois.forEach((poi, index) => {
      const isCompleted = completedStopIds.has(poi.id);
      const isActive = index === activeStopIndex;

      const row = document.createElement('div');
      row.className = 'route-stop-line';
      row.innerHTML = `
        <span class="stop-num-pill ${isCompleted ? 'completed' : (isActive ? 'active' : '')}">
          ${isCompleted ? '<span class="material-symbols-outlined" style="font-size:14px;">check</span>' : (index + 1)}
        </span>
        <span class="stop-name-text">${poi.name}</span>
        <span class="material-symbols-outlined stop-status-icon ${isCompleted ? 'done' : ''}">
          ${isCompleted ? 'check_circle' : (isActive ? 'navigation' : 'lock')}
        </span>
      `;
      row.addEventListener('click', () => {
        selectStop(index);
        showScreen('screen-map');
      });
      container.appendChild(row);
    });
  }

  // ══════════════════════════════════════════════════════════════
  // 6. SCREEN 2: LEAFLET TÉRKÉP ÉS GEOFENCING
  // ══════════════════════════════════════════════════════════════
  function initMap() {
    if (!tourData || map) return;

    const initialCenter = tourData.map_center || [47.5085, 19.0700];
    const initialZoom = tourData.default_zoom || 14;

    map = L.map('map-container', {
      zoomControl: false,
      attributionControl: false
    }).setView(initialCenter, initialZoom);

    // Zoom vezérlő jobb alsó sarokba
    L.control.zoom({ position: 'bottomright' }).addTo(map);

    // Térképcsempe téma szerint
    const currentTheme = document.body.classList.contains('theme-dark') ? 'dark' : 'light';
    updateMapTileTheme(currentTheme);

    // Útvonal Polyline rajzolása
    const latlngs = tourData.pois.map(p => p.coords);
    routePolyline = L.polyline(latlngs, {
      color: 'var(--track-base)',
      weight: 5,
      opacity: 0.8,
      lineCap: 'round',
      dashArray: '8, 8'
    }).addTo(map);

    // Megálló Markerek elhelyezése
    renderMapStopMarkers();

    // Lebegő vezérlők
    const btnRecenter = document.getElementById('btn-recenter-gps');
    if (btnRecenter) {
      btnRecenter.addEventListener('click', () => {
        if (userCoords) {
          map.setView(userCoords, 16, { animate: true });
        } else {
          centerMapOnActive();
        }
      });
    }

    const btnOpenTest = document.getElementById('btn-open-test');
    if (btnOpenTest) {
      btnOpenTest.addEventListener('click', openTestPanel);
    }

    // Térkép központosítása az aktív megállóra
    centerMapOnActive();
  }

  function renderMapStopMarkers() {
    if (!map || !tourData) return;

    // Régi markerek törlése
    stopMarkers.forEach(m => map.removeLayer(m));
    stopMarkers = [];

    tourData.pois.forEach((poi, index) => {
      const isCompleted = completedStopIds.has(poi.id);
      const isActive = index === activeStopIndex;

      let markerClass = 'kitero-marker';
      if (isCompleted) markerClass += ' completed';
      else if (isActive) markerClass += ' active';

      const icon = L.divIcon({
        className: 'custom-leaflet-marker',
        html: `<div class="${markerClass}">${isCompleted ? '<span class="material-symbols-outlined" style="font-size:16px;">check</span>' : (index + 1)}</div>`,
        iconSize: [32, 32],
        iconAnchor: [16, 16]
      });

      const marker = L.marker(poi.coords, { icon }).addTo(map);
      marker.on('click', () => {
        selectStop(index);
      });
      stopMarkers.push(marker);
    });

    updateCompletedPolyline();
  }

  function updateCompletedPolyline() {
    if (!map || !tourData) return;

    if (completedPolyline) {
      map.removeLayer(completedPolyline);
    }

    // Csak a már bejárt megállók vonala
    const completedCoords = [];
    for (let i = 0; i <= activeStopIndex; i++) {
      if (tourData.pois[i]) {
        completedCoords.push(tourData.pois[i].coords);
      }
    }

    if (completedCoords.length >= 2) {
      completedPolyline = L.polyline(completedCoords, {
        color: '#529B72',
        weight: 5,
        opacity: 0.9,
        lineCap: 'round'
      }).addTo(map);
    }
  }

  function centerMapOnActive() {
    if (!map || !tourData) return;
    const activePoi = tourData.pois[activeStopIndex];
    if (activePoi) {
      map.setView(activePoi.coords, 16, { animate: true });
    }
  }

  function selectStop(index) {
    if (!tourData || index < 0 || index >= tourData.pois.length) return;
    activeStopIndex = index;
    saveProgress();

    renderMapStopMarkers();
    updateHUD();
    updateStoryScreen();
    centerMapOnActive();
    renderBriefScreen();
  }

  // ══════════════════════════════════════════════════════════════
  // 7. GPS KÖVETÉS & GEOFENCE ÉRZÉKELÉS (35M)
  // ══════════════════════════════════════════════════════════════
  function startGeolocationTracking() {
    if (!('geolocation' in navigator)) {
      console.warn('Geolocation nem érhető el a böngészőben');
      // Alapértelmezett GPS koordináta az 1. megállótól 200m-re teszt kedvéért
      if (!userCoords && tourData && tourData.pois.length > 0) {
        userCoords = [tourData.pois[0].coords[0] - 0.0015, tourData.pois[0].coords[1] - 0.0015];
        updateUserPosition(userCoords[0], userCoords[1], 15);
      }
      return;
    }

    geoWatchId = navigator.geolocation.watchPosition(
      (pos) => {
        if (isSimulatedGPS) return; // Ne írjuk felül a szimulált tesztpozíciót
        updateUserPosition(pos.coords.latitude, pos.coords.longitude, pos.coords.accuracy);
      },
      (err) => {
        console.warn('GPS lekérési figyelmeztetés:', err.message);
        // Fallback: Ha még nincs pozíció, induljunk az 1. megálló közeléből
        if (!userCoords && tourData && tourData.pois.length > 0) {
          updateUserPosition(tourData.pois[0].coords[0] - 0.001, tourData.pois[0].coords[1] - 0.001, 20);
        }
      },
      {
        enableHighAccuracy: true,
        maximumAge: 5000,
        timeout: 10000
      }
    );
  }

  function updateUserPosition(lat, lng, accuracy) {
    userCoords = [lat, lng];
    userAccuracy = accuracy || 10;

    if (!map) return;

    // Felhasználói GPS Marker létrehozása vagy frissítése
    if (!userMarker) {
      const gpsIcon = L.divIcon({
        className: 'user-gps-container',
        html: '<div class="user-gps-marker"></div>',
        iconSize: [18, 18],
        iconAnchor: [9, 9]
      });
      userMarker = L.marker(userCoords, { icon: gpsIcon, zIndexOffset: 1000 }).addTo(map);

      accuracyCircle = L.circle(userCoords, {
        radius: Math.min(userAccuracy, 50),
        color: '#2563EB',
        fillColor: '#2563EB',
        fillOpacity: 0.12,
        weight: 1
      }).addTo(map);
    } else {
      userMarker.setLatLng(userCoords);
      if (accuracyCircle) {
        accuracyCircle.setLatLng(userCoords);
        accuracyCircle.setRadius(Math.min(userAccuracy, 50));
      }
    }

    checkGeofence();
    updateHUD();
    updateTestTelemetry();
  }

  function checkGeofence() {
    if (!userCoords || !tourData) return;
    const currentPoi = tourData.pois[activeStopIndex];
    if (!currentPoi) return;

    const distance = getDistanceMeters(userCoords[0], userCoords[1], currentPoi.coords[0], currentPoi.coords[1]);

    if (distance <= GEOFENCE_RADIUS_METERS) {
      onGeofenceArrival(currentPoi, distance);
    }
  }

  function onGeofenceArrival(poi, distance) {
    const isAlreadyCompleted = completedStopIds.has(poi.id);

    // HUD jelölés
    const distTag = document.getElementById('hud-distance-tag');
    const distVal = document.getElementById('hud-distance-val');
    if (distTag && distVal) {
      distTag.classList.add('arrived');
      distVal.textContent = `Megérkeztél! (${Math.round(distance)}m)`;
    }

    if (!isAlreadyCompleted) {
      showToast(`Megérkeztél a(z) ${poi.id}. állomáshoz: ${poi.name}!`, 'success');
      // Automatikus hang lejátszása ha még nem szól semmi
      if (!isAudioPlaying) {
        playAudio('hook');
      }
    }
  }

  // Távolság számítás (Haversine formula)
  function getDistanceMeters(lat1, lon1, lat2, lon2) {
    const R = 6371e3; // Föld sugara méterben
    const phi1 = lat1 * Math.PI / 180;
    const phi2 = lat2 * Math.PI / 180;
    const deltaPhi = (lat2 - lat1) * Math.PI / 180;
    const deltaLambda = (lon2 - lon1) * Math.PI / 180;

    const a = Math.sin(deltaPhi / 2) * Math.sin(deltaPhi / 2) +
      Math.cos(phi1) * Math.cos(phi2) *
      Math.sin(deltaLambda / 2) * Math.sin(deltaLambda / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

    return R * c;
  }

  function formatDistance(meters) {
    if (meters < 1000) {
      return `${Math.round(meters)} méterre`;
    }
    return `${(meters / 1000).toFixed(1)} km-re`;
  }

  // ══════════════════════════════════════════════════════════════
  // 8. HUD & MEGÁLLÓ ÁLLAPOT FRISSÍTÉSE
  // ══════════════════════════════════════════════════════════════
  function updateHUD() {
    if (!tourData) return;
    const poi = tourData.pois[activeStopIndex];
    if (!poi) return;

    const badgeEl = document.getElementById('hud-stop-badge');
    const nameEl = document.getElementById('hud-stop-name');
    const distTag = document.getElementById('hud-distance-tag');
    const distVal = document.getElementById('hud-distance-val');

    if (badgeEl) badgeEl.textContent = `${poi.id}. Megálló • ${poi.coords[0].toFixed(4)}° N`;
    if (nameEl) nameEl.textContent = poi.name;

    if (userCoords && distTag && distVal) {
      const distance = getDistanceMeters(userCoords[0], userCoords[1], poi.coords[0], poi.coords[1]);
      if (distance <= GEOFENCE_RADIUS_METERS) {
        distTag.classList.add('arrived');
        distVal.textContent = `Megérkeztél! (${Math.round(distance)}m)`;
      } else {
        distTag.classList.remove('arrived');
        distVal.textContent = formatDistance(distance);
      }
    } else if (distVal) {
      distVal.textContent = 'GPS keresés...';
    }

    const btnOpenStory = document.getElementById('hud-btn-open-story');
    if (btnOpenStory) {
      btnOpenStory.onclick = () => showScreen('screen-story');
    }
  }

  // ══════════════════════════════════════════════════════════════
  // 9. SCREEN 3: TÖRTÉNET, ADATMÁTRIX ÉS PODCAST AUDIO (TTS FALLBACK)
  // ══════════════════════════════════════════════════════════════
  function updateStoryScreen() {
    if (!tourData) return;
    const poi = tourData.pois[activeStopIndex];
    if (!poi) return;

    const isCompleted = completedStopIds.has(poi.id);

    // Kép és feloldás jelvény
    const photoEl = document.getElementById('story-photo');
    if (photoEl) {
      photoEl.src = poi.photo || 'https://images.unsplash.com/photo-1541872703-74c5e44368f9?auto=format&fit=crop&w=800&q=80';
      photoEl.alt = poi.name;
    }

    const unlockText = document.getElementById('story-unlock-text');
    if (unlockText) {
      unlockText.textContent = `${poi.id}. Titok ${isCompleted ? 'feloldva' : 'helyszíni archívum'}`;
    }

    const titleEl = document.getElementById('story-stop-title');
    const addressEl = document.getElementById('story-stop-address');
    if (titleEl) titleEl.textContent = poi.name;
    if (addressEl) addressEl.textContent = poi.address || 'Budapest';

    // 4 részes Adatmátrix
    const matrix = poi.matrix || {
      year: '1896',
      style: 'Historizmus',
      function_change: 'Közlekedés',
      historical_weight: 'Millenniumi emlék'
    };

    const yearEl = document.getElementById('matrix-year');
    const styleEl = document.getElementById('matrix-style');
    const funcEl = document.getElementById('matrix-function');
    const histEl = document.getElementById('matrix-historical');

    if (yearEl) yearEl.textContent = matrix.year;
    if (styleEl) styleEl.textContent = matrix.style;
    if (funcEl) funcEl.textContent = matrix.function_change;
    if (histEl) histEl.textContent = matrix.historical_weight;

    // Szövegtörzs
    const fullTextEl = document.getElementById('story-full-text');
    if (fullTextEl) {
      fullTextEl.textContent = poi.audio_story || poi.desc || '';
    }

    // Teljesítés gomb felirat
    const btnComplete = document.getElementById('btn-complete-stop');
    const completeText = document.getElementById('btn-complete-text');
    if (btnComplete && completeText) {
      const nextNum = activeStopIndex + 2;
      if (activeStopIndex === tourData.pois.length - 1) {
        completeText.textContent = 'Séta Befejezése & Oklevél átvétele!';
      } else {
        completeText.textContent = `Megálló teljesítve (Következő: ${nextNum}/${tourData.pois.length})`;
      }

      btnComplete.onclick = () => completeCurrentStop();
    }

    resetAudioProgress();
  }

  function completeCurrentStop() {
    if (!tourData) return;
    const poi = tourData.pois[activeStopIndex];
    if (poi) {
      completedStopIds.add(poi.id);
    }

    // Hang leállítása léptetéskor
    stopAudio();

    if (completedStopIds.size >= tourData.pois.length) {
      isFinished = true;
      saveProgress();
      updateGestaltRing();
      renderVaultList();
      renderBriefScreen();
      renderMapStopMarkers();
      showScreen('screen-finish');
      showToast('Gratulálunk! Mind a 9 megállót sikeresen bejártad!', 'success');
      return;
    }

    // Következő megállóra ugrás
    if (activeStopIndex < tourData.pois.length - 1) {
      activeStopIndex++;
    }
    saveProgress();
    updateGestaltRing();
    renderBriefScreen();
    renderMapStopMarkers();
    updateHUD();
    updateStoryScreen();
    showScreen('screen-map');
    showToast(`${poi.name} teljesítve! Haladj a következő megállóhoz.`);
  }

  // ══════════════════════════════════════════════════════════════
  // 10. AUDIO LEJÁTSZÓ & WEB SPEECH API TTS FALLBACK
  // ══════════════════════════════════════════════════════════════
  function setupAudioDeck() {
    const tabHook = document.getElementById('tab-audio-hook');
    const tabStory = document.getElementById('tab-audio-story');

    if (tabHook && tabStory) {
      tabHook.addEventListener('click', () => {
        tabHook.classList.add('active');
        tabStory.classList.remove('active');
        audioMode = 'hook';
        resetAudioProgress();
      });

      tabStory.addEventListener('click', () => {
        tabStory.classList.add('active');
        tabHook.classList.remove('active');
        audioMode = 'story';
        resetAudioProgress();
      });
    }

    // Lejátszás / Szünet gombok (HUD és Történet nézet szinkronban)
    const hudBtnPlay = document.getElementById('hud-btn-play');
    const storyBtnPlay = document.getElementById('story-btn-play');

    if (hudBtnPlay) {
      hudBtnPlay.addEventListener('click', toggleAudio);
    }
    if (storyBtnPlay) {
      storyBtnPlay.addEventListener('click', toggleAudio);
    }

    // 10 másodperc ugrás
    const btnSkipBack = document.getElementById('btn-skip-back');
    const btnSkipFwd = document.getElementById('btn-skip-fwd');

    if (btnSkipBack) {
      btnSkipBack.addEventListener('click', () => {
        audioElapsedSec = Math.max(0, audioElapsedSec - 10);
        updateAudioProgressUI();
      });
    }

    if (btnSkipFwd) {
      btnSkipFwd.addEventListener('click', () => {
        audioElapsedSec = Math.min(audioTotalSec, audioElapsedSec + 10);
        updateAudioProgressUI();
      });
    }

    // Lejátszási sebesség
    const btnRate = document.getElementById('btn-playback-rate');
    if (btnRate) {
      btnRate.addEventListener('click', () => {
        if (playbackRate === 1.0) playbackRate = 1.25;
        else if (playbackRate === 1.25) playbackRate = 1.5;
        else playbackRate = 1.0;

        btnRate.textContent = `${playbackRate.toFixed(1)}x`;
        if (isAudioPlaying) {
          // Újraindítás új sebességgel
          playAudio(audioMode);
        }
      });
    }

    // Csúszka kattintás
    const storyTrack = document.getElementById('story-audio-track');
    if (storyTrack) {
      storyTrack.addEventListener('click', (e) => {
        const rect = storyTrack.getBoundingClientRect();
        const ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
        audioElapsedSec = Math.round(ratio * audioTotalSec);
        if (nativeAudio && nativeAudio.src) {
          nativeAudio.currentTime = audioElapsedSec;
        }
        updateAudioProgressUI();
      });
    }

    // Lebegő globális player események
    const globalBtnPlay = document.getElementById('global-btn-play');
    if (globalBtnPlay) {
      globalBtnPlay.addEventListener('click', toggleAudio);
    }
    const globalBtnClose = document.getElementById('global-btn-close');
    if (globalBtnClose) {
      globalBtnClose.addEventListener('click', () => {
        stopAudio();
        const globalPlayer = document.getElementById('floating-global-player');
        if (globalPlayer) globalPlayer.style.display = 'none';
      });
    }
    const globalTrackInfo = document.getElementById('global-track-info');
    if (globalTrackInfo) {
      globalTrackInfo.addEventListener('click', () => {
        showScreen('screen-story');
      });
    }

    // HTML5 nativeAudio eseménykezelők a Piper hangokhoz
    nativeAudio.addEventListener('ended', onAudioFinished);
    nativeAudio.addEventListener('error', (e) => {
      console.warn('Helyi Piper WAV hiba, fallback WebSpeech-re', e);
      fallbackWebSpeech(audioMode);
    });
    nativeAudio.addEventListener('timeupdate', () => {
      if (nativeAudio.duration) {
        audioElapsedSec = Math.round(nativeAudio.currentTime);
        audioTotalSec = Math.round(nativeAudio.duration);
        updateAudioProgressUI();
      }
    });
  }

  function toggleAudio() {
    if (isAudioPlaying) {
      pauseAudio();
    } else {
      playAudio(audioMode);
    }
  }

  function playAudio(mode) {
    if (!tourData) return;
    const poi = tourData.pois[activeStopIndex];
    if (!poi) return;

    audioMode = mode;
    const globalPlayer = document.getElementById('floating-global-player');
    const globalTitle = document.getElementById('global-track-title');
    if (globalPlayer) globalPlayer.style.display = 'flex';
    if (globalTitle) globalTitle.textContent = `${activeStopIndex + 1}. ${poi.name} (${mode === 'hook' ? 'Felütés' : 'Történet'})`;

    // Piper Imre hangfájl betöltése a helyi /audio/ mappából
    const audioUrl = `/app/audio/poi_${poi.id}_${mode}.wav`;
    
    // Ha a böngésző már ezt játssza vagy betöltötte
    if (nativeAudio.src && nativeAudio.src.includes(`poi_${poi.id}_${mode}.wav`) && nativeAudio.currentTime > 0 && !nativeAudio.ended) {
      nativeAudio.play().then(() => {
        isAudioPlaying = true;
        updateAudioPlayIcons();
      }).catch(err => {
        console.error('Audio play hiba:', err);
      });
      return;
    }

    nativeAudio.pause();
    nativeAudio.src = audioUrl;
    nativeAudio.playbackRate = playbackRate;
    nativeAudio.load();
    nativeAudio.play().then(() => {
      isAudioPlaying = true;
      updateAudioPlayIcons();
      showToast('Piper Imre hanganyaga megszólalt.');
    }).catch(err => {
      console.error('Audio play sikertelen, fallback speechre:', err);
      fallbackWebSpeech(mode);
    });
  }

  function fallbackWebSpeech(mode) {
    if (!tourData) return;
    const poi = tourData.pois[activeStopIndex];
    if (!poi) return;

    const textToSpeak = mode === 'hook'
      ? (poi.audio_hook || poi.hook || poi.name)
      : (poi.audio_story || poi.desc || poi.name);

    const words = textToSpeak.split(/\s+/).length;
    audioTotalSec = Math.max(15, Math.round((words / 140) * 60 / playbackRate));

    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      activeUtterance = new SpeechSynthesisUtterance(textToSpeak);
      activeUtterance.lang = 'hu-HU';
      activeUtterance.rate = playbackRate;

      const voices = window.speechSynthesis.getVoices();
      const huVoice = voices.find(v => v.lang.startsWith('hu'));
      if (huVoice) activeUtterance.voice = huVoice;

      activeUtterance.onend = onAudioFinished;
      activeUtterance.onerror = pauseAudio;
      window.speechSynthesis.speak(activeUtterance);
    }

    isAudioPlaying = true;
    updateAudioPlayIcons();

    clearInterval(audioTimer);
    audioTimer = setInterval(() => {
      audioElapsedSec++;
      updateAudioProgressUI();
      if (audioElapsedSec >= audioTotalSec) {
        onAudioFinished();
      }
    }, 1000);
  }

  function pauseAudio() {
    isAudioPlaying = false;
    clearInterval(audioTimer);
    if (nativeAudio) {
      nativeAudio.pause();
    }
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    updateAudioPlayIcons();
  }

  function stopAudio() {
    pauseAudio();
    if (nativeAudio) {
      nativeAudio.currentTime = 0;
    }
    resetAudioProgress();
  }

  function onAudioFinished() {
    pauseAudio();
    audioElapsedSec = audioTotalSec;
    updateAudioProgressUI();
  }

  function resetAudioProgress() {
    audioElapsedSec = 0;
    if (nativeAudio && nativeAudio.src) {
      nativeAudio.currentTime = 0;
    }
    updateAudioProgressUI();
  }

  function updateAudioPlayIcons() {
    const hudIcon = document.getElementById('hud-audio-icon');
    const storyIcon = document.getElementById('story-play-icon');
    const globalIcon = document.getElementById('global-play-icon');

    const iconName = isAudioPlaying ? 'pause' : 'play_arrow';
    if (hudIcon) hudIcon.textContent = iconName;
    if (storyIcon) storyIcon.textContent = iconName;
    if (globalIcon) globalIcon.textContent = iconName;
  }

  function updateAudioProgressUI() {
    const hudBar = document.getElementById('hud-audio-bar');
    const storyBar = document.getElementById('story-audio-bar');
    const globalBar = document.getElementById('global-progress-bar');
    const hudCur = document.getElementById('hud-audio-current');
    const hudDur = document.getElementById('hud-audio-duration');
    const storyCur = document.getElementById('story-audio-current');
    const storyDur = document.getElementById('story-audio-duration');
    const globalElapsed = document.getElementById('global-time-elapsed');
    const globalTotal = document.getElementById('global-time-total');

    const pct = audioTotalSec > 0 ? (audioElapsedSec / audioTotalSec) * 100 : 0;
    if (hudBar) hudBar.style.width = `${pct}%`;
    if (storyBar) storyBar.style.width = `${pct}%`;
    if (globalBar) globalBar.style.width = `${pct}%`;

    const curStr = formatTime(audioElapsedSec);
    const durStr = `${formatTime(audioTotalSec)}`;

    if (hudCur) hudCur.textContent = curStr;
    if (hudDur) hudDur.textContent = `${durStr} (Piper)`;
    if (storyCur) storyCur.textContent = curStr;
    if (storyDur) storyDur.textContent = `${durStr} (Piper)`;
    if (globalElapsed) globalElapsed.textContent = curStr;
    if (globalTotal) globalTotal.textContent = durStr;
  }
  }

  function formatTime(sec) {
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  }

  // ══════════════════════════════════════════════════════════════
  // 11. SCREEN 4: BEFEJEZÉS & DIPLOMA
  // ══════════════════════════════════════════════════════════════
  function renderVaultList() {
    if (!tourData) return;
    const container = document.getElementById('vault-items-list');
    if (!container) return;

    container.innerHTML = '';
    tourData.pois.forEach((poi) => {
      const isUnlocked = completedStopIds.has(poi.id);
      const row = document.createElement('div');
      row.className = 'vault-row';
      row.innerHTML = `
        <div class="vault-left">
          <span class="material-symbols-outlined" style="font-size:16px; color:${isUnlocked ? 'var(--accent)' : 'var(--text-dim)'};">
            ${isUnlocked ? 'check_circle' : 'lock'}
          </span>
          <span>${poi.id}. ${poi.name}</span>
        </div>
        <span style="font-size:11px; color:${isUnlocked ? 'var(--accent)' : 'var(--text-dim)'}; font-weight:700;">
          ${isUnlocked ? 'Feloldva' : 'Zárolt'}
        </span>
      `;
      container.appendChild(row);
    });

    // Eltelt idő kiszámítása
    const elapsedEl = document.getElementById('diploma-elapsed-time');
    if (elapsedEl && startTime) {
      const now = new Date();
      const diffMinutes = Math.max(1, Math.round((now - startTime) / (1000 * 60)));
      const h = Math.floor(diffMinutes / 60);
      const m = diffMinutes % 60;
      elapsedEl.textContent = h > 0 ? `${h}ó ${m}p` : `${m} perc`;
    }
  }

  function setupDiplomaActions() {
    const btnShare = document.getElementById('btn-share-walk');
    if (btnShare) {
      btnShare.addEventListener('click', () => {
        const shareData = {
          title: 'VitaSteps Kitérő — Városi Felfedező Oklevél',
          text: 'Sikeresen teljesítettem A Kisföldalatti Nyomában élménysétát (3.4 km, 9/9 feltárt titok)!',
          url: window.location.href
        };

        if (navigator.share) {
          navigator.share(shareData).catch(() => {});
        } else {
          // Vágólapra másolás fallback
          navigator.clipboard.writeText(`${shareData.title}\n${shareData.text}\n${shareData.url}`)
            .then(() => showToast('Oklevél szövege a vágólapra másolva!', 'success'))
            .catch(() => showToast('Oklevél megosztás kész!'));
        }
      });
    }

    const btnReplay = document.getElementById('btn-replay-walk');
    if (btnReplay) {
      btnReplay.addEventListener('click', () => {
        if (confirm('Biztosan újra szeretnéd játszani a sétát az elejétől?')) {
          resetAllProgress();
        }
      });
    }
  }

  // ══════════════════════════════════════════════════════════════
  // 12. SCREEN 5: PROFIL & BEAVATOTTI STÁTUSZ
  // ══════════════════════════════════════════════════════════════
  function updateProfileScreen() {
    if (!tourData) return;
    const completedCount = completedStopIds.size;
    const total = tourData.pois.length;

    const rankEl = document.getElementById('profile-rank');
    const statsEl = document.getElementById('profile-stats-summary');
    const guideStatus = document.getElementById('profile-guide-status');

    if (rankEl) {
      rankEl.textContent = completedCount >= total ? 'Fővárosi Városkutató' : 'Kezdő Városfelfedező';
    }

    if (statsEl) {
      statsEl.textContent = `${completedCount >= total ? '1' : '0'} teljesített séta • ${completedCount} titok a zsebben`;
    }

    if (guideStatus) {
      guideStatus.textContent = `${completedCount} / ${total} Kész`;
    }

    const btnReset = document.getElementById('btn-profile-reset');
    if (btnReset) {
      btnReset.onclick = () => {
        if (confirm('Törlöd a helyi haladást és elölről kezded a sétát?')) {
          resetAllProgress();
        }
      };
    }
  }

  function resetAllProgress() {
    localStorage.removeItem(STORAGE_KEY);
    completedStopIds.clear();
    activeStopIndex = 0;
    isFinished = false;
    startTime = new Date();

    stopAudio();
    updateGestaltRing();
    renderBriefScreen();
    renderMapStopMarkers();
    updateHUD();
    updateStoryScreen();
    renderVaultList();
    updateProfileScreen();
    showScreen('screen-brief');
    showToast('Haladás törölve. Kellemes újrafelfedezést!');
  }

  // ══════════════════════════════════════════════════════════════
  // 13. TESZT ÜZEMMÓD & GPS SZIMULÁTOR
  // ══════════════════════════════════════════════════════════════
  function setupTestMode() {
    const btnTestToggle = document.getElementById('test-mode-toggle-btn');
    if (btnTestToggle) {
      btnTestToggle.addEventListener('click', openTestPanel);
    }

    const btnCloseTest = document.getElementById('btn-close-test');
    if (btnCloseTest) {
      btnCloseTest.addEventListener('click', closeTestPanel);
    }

    // Következő léptetés
    const btnNext = document.getElementById('test-btn-next');
    if (btnNext) {
      btnNext.addEventListener('click', () => {
        if (!tourData) return;
        teleportToStop(activeStopIndex);
        completeCurrentStop();
      });
    }

    // Összes azonnali feloldása
    const btnUnlockAll = document.getElementById('test-btn-unlock-all');
    if (btnUnlockAll) {
      btnUnlockAll.addEventListener('click', () => {
        if (!tourData) return;
        tourData.pois.forEach(p => completedStopIds.add(p.id));
        isFinished = true;
        saveProgress();
        updateGestaltRing();
        renderVaultList();
        renderBriefScreen();
        renderMapStopMarkers();
        updateProfileScreen();
        closeTestPanel();
        showScreen('screen-finish');
        showToast('Teszt: Mind a 9 megálló feloldva!', 'success');
      });
    }

    // Valós GPS visszaállítása
    const btnRealGPS = document.getElementById('test-btn-real-gps');
    if (btnRealGPS) {
      btnRealGPS.addEventListener('click', () => {
        isSimulatedGPS = false;
        showToast('Valós GPS nyomkövetés aktív.');
        startGeolocationTracking();
      });
    }

    // Nullázás
    const btnReset = document.getElementById('test-btn-reset-data');
    if (btnReset) {
      btnReset.addEventListener('click', () => {
        resetAllProgress();
        closeTestPanel();
      });
    }
  }

  function openTestPanel() {
    renderTestGrid();
    const overlay = document.getElementById('test-panel-overlay');
    if (overlay) overlay.classList.add('active');
    updateTestTelemetry();
  }

  function closeTestPanel() {
    const overlay = document.getElementById('test-panel-overlay');
    if (overlay) overlay.classList.remove('active');
  }

  function renderTestGrid() {
    if (!tourData) return;
    const grid = document.getElementById('test-stops-grid');
    if (!grid) return;

    grid.innerHTML = '';
    tourData.pois.forEach((poi, index) => {
      const btn = document.createElement('button');
      btn.className = `test-poi-btn ${index === activeStopIndex ? 'active' : ''}`;
      btn.textContent = `${poi.id}. ${poi.name.split(' ')[0]}`;
      btn.title = poi.name;
      btn.addEventListener('click', () => {
        teleportToStop(index);
      });
      grid.appendChild(btn);
    });
  }

  function teleportToStop(index) {
    if (!tourData || !tourData.pois[index]) return;
    const targetPoi = tourData.pois[index];

    // Szimulált GPS: a cél megállótól pontosan 10 méterre
    isSimulatedGPS = true;
    const simLat = targetPoi.coords[0] + 0.00008;
    const simLng = targetPoi.coords[1] + 0.00008;

    selectStop(index);
    updateUserPosition(simLat, simLng, 5);

    if (map) {
      map.setView([simLat, simLng], 17, { animate: true });
    }

    renderTestGrid();
    showToast(`Teleportálva: ${targetPoi.name} (10m)`, 'success');
  }

  function updateTestTelemetry() {
    const dump = document.getElementById('test-telemetry-dump');
    if (!dump || !tourData) return;

    const currentPoi = tourData.pois[activeStopIndex];
    const dist = userCoords && currentPoi
      ? Math.round(getDistanceMeters(userCoords[0], userCoords[1], currentPoi.coords[0], currentPoi.coords[1]))
      : 'N/A';

    dump.textContent = `GPS: ${isSimulatedGPS ? 'SZIMULÁLT' : 'ÉLES'} | Cél: ${currentPoi?.name || 'N/A'} | Táv: ${dist}m | Geofence: 35m`;
  }

  // ══════════════════════════════════════════════════════════════
  // 14. SCREEN WAKE LOCK API
  // ══════════════════════════════════════════════════════════════
  function setupWakeLock() {
    const btnWake = document.getElementById('btn-wakelock');
    if (btnWake) {
      btnWake.addEventListener('click', toggleWakeLock);
    }
  }

  async function requestWakeLock() {
    if ('wakeLock' in navigator) {
      try {
        wakeLockSentinel = await navigator.wakeLock.request('screen');
        updateWakeLockUI(true);
        wakeLockSentinel.addEventListener('release', () => {
          updateWakeLockUI(false);
          wakeLockSentinel = null;
        });
      } catch (err) {
        console.warn('WakeLock kérelem sikertelen:', err);
      }
    }
  }

  function toggleWakeLock() {
    if (wakeLockSentinel) {
      wakeLockSentinel.release();
      wakeLockSentinel = null;
      updateWakeLockUI(false);
      showToast('Képernyő ébrentartása kikapcsolva.');
    } else {
      requestWakeLock();
      showToast('Képernyő ébrentartása bekapcsolva séta közben.');
    }
  }

  function updateWakeLockUI(active) {
    const btnWake = document.getElementById('btn-wakelock');
    if (btnWake) {
      btnWake.classList.toggle('active', active);
    }
  }

  // ══════════════════════════════════════════════════════════════
  // 15. TOAST ÉRTESÍTÉSEK
  // ══════════════════════════════════════════════════════════════
  let toastTimer = null;
  function showToast(message, type) {
    const toast = document.getElementById('toast-notice');
    const toastText = document.getElementById('toast-text');
    const toastIcon = document.getElementById('toast-icon');

    if (!toast || !toastText) return;

    toastText.textContent = message;
    if (toastIcon) {
      toastIcon.textContent = type === 'error' ? 'error' : (type === 'success' ? 'verified' : 'info');
    }

    toast.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
      toast.classList.remove('show');
    }, 3500);
  }

})();
