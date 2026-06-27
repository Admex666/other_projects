// ===== COUNTDOWN =====
const CAMPAIGN_END = new Date('2026-08-31T23:59:59');

function updateCountdown() {
    const now = new Date();
    const diff = CAMPAIGN_END - now;
    if (diff <= 0) {
        const countdownEl = document.getElementById('countdown');
        if (countdownEl) {
            countdownEl.innerHTML = '<span style="color:var(--text-mid); font-weight: 600;">A nevezés lezárult. Később új kihívással jelentkezünk!</span>';
        }

        document.querySelectorAll('#hero-cta, #nav-cta, .sticky-cta-mobile a, #checkout-section-btn').forEach(btn => {
            btn.style.pointerEvents = 'none';
            btn.style.opacity = '0.5';
            if (btn.id === 'checkout-section-btn') {
                btn.innerHTML = 'Nevezés lezárult';
            } else {
                btn.textContent = 'Nevezés lezárult';
            }
        });

        const badge = document.getElementById('badge-earlybird');
        if (badge) {
            badge.innerHTML = 'Kihívás lezárva';
            badge.style.background = 'rgba(255,255,255,0.08)';
            badge.style.color = 'var(--text-high)';
        }
        return;
    }
    const d = Math.floor(diff / (1000 * 60 * 60 * 24));
    const h = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const m = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    const s = Math.floor((diff % (1000 * 60)) / 1000);
    document.getElementById('cd-days').textContent = String(d).padStart(2, '0');
    document.getElementById('cd-hours').textContent = String(h).padStart(2, '0');
    document.getElementById('cd-mins').textContent = String(m).padStart(2, '0');
    document.getElementById('cd-secs').textContent = String(s).padStart(2, '0');
}
updateCountdown();
setInterval(updateCountdown, 1000);

// ===== META PIXEL EVENTS =====
document.getElementById('payment-btn')?.addEventListener('click', () => {
    if (typeof fbq !== 'undefined') {
        fbq('track', 'InitiateCheckout', { value: 7990, currency: 'HUF' });
    }
});

document.getElementById('hero-cta')?.addEventListener('click', () => {
    if (typeof fbq !== 'undefined') {
        fbq('track', 'ViewContent', { content_name: 'Prédikálószék Kihívás' });
    }
});

document.getElementById('nav-cta')?.addEventListener('click', () => {
    if (typeof fbq !== 'undefined') {
        fbq('track', 'ViewContent', { content_name: 'Prédikálószék Kihívás - Nav CTA' });
    }
});

// ===== MAP & GPX INITIALIZATION =====
let mapInstance = null;
let currentGpxLayer = null;

const routeMap = {
    'domos_10': 'assets/predikalo_dömös10.8.gpx',
    'domos_15': 'assets/predikalo_dömös17.3.gpx',
    'domos_20': 'assets/predikalo_dömös21.6.gpx',
    'domos_25': 'assets/predikalo_dömös25.4.gpx',
    'dobogoko_10': 'assets/predikalo_dobogoko9.5.gpx',
    'dobogoko_15': 'assets/predikalo_dobogoko15.2.gpx',
    'dobogoko_20': 'assets/predikalo_dobogoko21.2.gpx',
    'dobogoko_25': 'assets/predikalo_dobogoko25.6.gpx'
};

let selectedStart = 'domos';
let selectedDist = '10';

function loadMap() {
    const mapEl = document.getElementById('map');
    const fallbackEl = document.getElementById('map-fallback');
    const downloadBtn = document.getElementById('download-btn');
    const downloadWrapper = document.getElementById('download-wrapper');
    const statsEl = document.getElementById('route-stats');

    if (!mapEl) return;

    if (!mapInstance) {
        mapInstance = L.map('map').setView([47.76, 18.91], 12);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap contributors'
        }).addTo(mapInstance);
    }

    const routeKey = `${selectedStart}_${selectedDist}`;
    const gpxFile = routeMap[routeKey];

    if (currentGpxLayer) {
        mapInstance.removeLayer(currentGpxLayer);
        currentGpxLayer = null;
    }

    if (gpxFile) {
        mapEl.style.display = 'block';
        fallbackEl.style.display = 'none';
        downloadWrapper.style.display = 'block';
        downloadBtn.href = gpxFile;

        fetch(gpxFile)
            .then(response => {
                if (!response.ok) throw new Error("Network error");
                return response.text();
            })
            .then(gpxData => {
                currentGpxLayer = new L.GPX(gpxData, {
                    async: true,
                    marker_options: {
                        startIconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet-gpx/1.7.0/pin-icon-start.png',
                        endIconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet-gpx/1.7.0/pin-icon-end.png',
                        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet-gpx/1.7.0/pin-shadow.png'
                    },
                    polyline_options: {
                        color: '#c4ff00',
                        weight: 5,
                        opacity: 0.9
                    }
                }).on('loaded', function (e) {
                    mapInstance.fitBounds(e.target.getBounds());
                    if (statsEl) {
                        statsEl.style.display = 'flex';
                        document.getElementById('stat-dist').textContent = (e.target.get_distance() / 1000).toFixed(1) + ' km';
                        document.getElementById('stat-elev').textContent = Math.round(e.target.get_elevation_gain()) + ' m';
                    }
                }).addTo(mapInstance);
            })
            .catch(error => {
                console.error("GPX fetch hiba:", error);
                alert("⚠️ A térkép nyomvonala biztonsági okokból (CORS) nem tud betölteni, mert a böngésződ blokkolja a helyi fájlok (file:///) beolvasását.\n\nA vonal tökéletesen fog látszani, amint feltöltöd Vercel-re, vagy ha VS Code 'Live Server'-t használsz!");
            });
    } else {
        mapEl.style.display = 'none';
        fallbackEl.style.display = 'flex';
        downloadWrapper.style.display = 'none';
        if (statsEl) statsEl.style.display = 'none';
    }
}

document.querySelectorAll('#btn-group-start .filter-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
        document.querySelectorAll('#btn-group-start .filter-btn').forEach(b => b.classList.remove('active'));
        e.target.classList.add('active');
        selectedStart = e.target.getAttribute('data-start');
        loadMap();
    });
});

document.querySelectorAll('#btn-group-dist .filter-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
        document.querySelectorAll('#btn-group-dist .filter-btn').forEach(b => b.classList.remove('active'));
        e.target.classList.add('active');
        selectedDist = e.target.getAttribute('data-dist');
        loadMap();
    });
});

if (document.getElementById('map')) {
    loadMap();
}

// ===== REDIRECT TO CHECKOUT WIDGET =====
document.querySelectorAll('#hero-cta, #nav-cta, .sticky-cta-mobile a, #checkout-section-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
        e.preventDefault();
        
        if (typeof fbq === 'function') {
            fbq('track', 'InitiateCheckout', { value: 7990, currency: 'HUF' });
        }
        
        window.location.href = `checkout-widget.html?distance=${selectedDist}%20km`;
    });
});

// ===== LEADERBOARD RENDERING =====
async function loadLeaderboard() {
    const listEl = document.getElementById('leaderboard-list');
    const countEl = document.getElementById('leaderboard-count');
    if (!listEl) return;

    try {
        const response = await fetch('/api/leaderboard');
        if (!response.ok) throw new Error('API hiba');
        const data = await response.json();
        
        if (countEl) {
            countEl.textContent = data.totalFinishers;
        }

        if (!data.users || data.users.length === 0) {
            listEl.innerHTML = '<div style="text-align: center; color: var(--text-mid); padding: 2rem;">Még nincsenek teljesítők. Legyél te az első!</div>';
            return;
        }

        // Render users
        let html = '';
        data.users.forEach((user, index) => {
            const rankNum = String(index + 1).padStart(2, '0');
            const statusClass = user.finished ? 'status-finished' : 'status-ongoing';
            const statusLabel = user.finished ? '✅ Teljesítve' : '⏳ Folyamatban';
            
            html += `
                <div class="leaderboard-item ${statusClass}">
                    <div class="leaderboard-rank">#${rankNum}</div>
                    <div class="leaderboard-name">
                        <span>${escapeHtml(user.name)}</span>
                        <span class="leaderboard-county">${escapeHtml(user.county)}</span>
                    </div>
                    <div class="leaderboard-info">
                        <span class="leaderboard-distance">🏔️ ${escapeHtml(user.distance)}</span>
                        <span class="leaderboard-status">${statusLabel}</span>
                    </div>
                </div>
            `;
        });
        listEl.innerHTML = html;
    } catch (err) {
        console.error('Nem sikerült betölteni a ranglistát:', err);
        listEl.innerHTML = '<div style="text-align: center; color: #ff6b6b; padding: 2rem;">⚠️ Hiba történt a ranglista betöltésekor. Kérjük próbáld újra később!</div>';
    }
}

function escapeHtml(str) {
    if (!str) return '';
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Call on load
loadLeaderboard();
