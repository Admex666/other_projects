// ===== COUNTDOWN =====
const CAMPAIGN_END = new Date('2026-06-23T23:59:59');

function updateCountdown() {
    const now = new Date();
    const diff = CAMPAIGN_END - now;
    if (diff <= 0) {
        const countdownEl = document.getElementById('countdown');
        if (countdownEl) {
            countdownEl.innerHTML = '<span style="color:var(--text-mid); font-weight: 600;">A nevezés lezárult. Később új kihívással jelentkezünk!</span>';
        }

        const heroCta = document.getElementById('hero-cta');
        if (heroCta) {
            heroCta.style.pointerEvents = 'none';
            heroCta.style.opacity = '0.5';
            heroCta.innerHTML = 'Nevezés lezárult';
        }

        const paymentBtn = document.getElementById('payment-btn');
        if (paymentBtn) {
            paymentBtn.style.pointerEvents = 'none';
            paymentBtn.style.opacity = '0.5';
            paymentBtn.innerHTML = 'Nevezés lezárult';
        }

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
    'dobogoko_20': 'assets/predikalo_dobogoko20.7.gpx',
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
