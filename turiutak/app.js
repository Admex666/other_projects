/**
 * TuristaÚt Kalandtervező - Application Logic
 */

// Application State
const state = {
    theme: 'dark',
    isPlanning: false,
    stops: [], // Array of L.marker
    plannedRoute: null, // L.polyline for solved route
    plannedCoordinates: null, // Array of [lon, lat]
    plannedMetrics: null, // Object with length, time, gain, loss
    highlightedLayer: null, // L.geoJSON for highlighted/searched trails
    wmsLayer: null, // L.esri.dynamicMapLayer for entire network
    activeSignFilter: null, // Active trail mark string
};

// Coded values mappings from ArcGIS Server
const roadTypes = {
    1: 'ösvény, gyalogút',
    2: 'járda, sétaút',
    3: 'szekérút',
    4: 'murvás út, erdei feltáróút',
    5: 'aszfaltozott út',
    6: 'betonozott út',
    7: 'fa pallóút',
    8: 'lépcső'
};

const surfTypes = {
    1: 'földes, füves',
    2: 'köves, murvás, sziklás',
    3: 'homokos',
    4: 'aszfalt, beton, térkő',
    5: 'fa',
    6: 'egyéb'
};

// Initialize Map
const map = L.map('map', {
    center: [47.1624, 19.5033], // Center of Hungary
    zoom: 8,
    zoomControl: false // Custom controls in top-right / sidebar
});

// Add custom zoom control to top-right
L.control.zoom({ position: 'topright' }).addTo(map);

// Map Base layers
const basemaps = {
    dark: L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 20
    }),
    light: L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 20
    })
};

// Set initial base layer
basemaps.dark.addTo(map);

// Initialize WMS/MapServer overlay layer for the tourist network
state.wmsLayer = L.esri.dynamicMapLayer({
    url: 'https://turistaterkepek.hu/server/rest/services/Turistaut_nyilvantartas/nyilvantartaswms/MapServer',
    opacity: 0.85,
    useCors: true
}).addTo(map);

// Create layer groups for routing stops & highlighting
const stopsGroup = L.layerGroup().addTo(map);

// Remove loading screen when map is ready
map.whenReady(() => {
    document.getElementById('app-loader').classList.add('hidden');
    lucide.createIcons();
});

// API endpoints
const API = {
    featureLayer: 'https://turistaterkepek.hu/server/rest/services/Turistaut_nyilvantartas/validalt_utszakaszok/FeatureServer/1',
    routingSolve: 'https://turistaterkepek.hu/server/rest/services/Routing/NetworkAnalysis/NAServer/Route/solve'
};

/**
 * Perform query on FeatureServer Layer 1
 */
async function queryFeatureLayer(where, geometry = null) {
    let url = `${API.featureLayer}/query?outFields=*&f=geojson&outSR=4326`;
    
    if (where) {
        url += `&where=${encodeURIComponent(where)}`;
    } else {
        url += `&where=1%3D1`;
    }

    if (geometry) {
        url += `&geometry=${encodeURIComponent(JSON.stringify(geometry))}&geometryType=esriGeometryEnvelope&spatialReference=%7B%22wkid%22%3A4326%7D&inSR=4326`;
    }

    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error('REST Query failed');
        return await response.json();
    } catch (error) {
        console.error('Error querying ArcGIS REST API:', error);
        showApiStatus(false, 'Hiba a lekérdezésben');
        return null;
    }
}

/**
 * Highlight features on the map using GeoJSON
 */
function highlightFeatures(geojson) {
    if (state.highlightedLayer) {
        map.removeLayer(state.highlightedLayer);
    }

    if (!geojson || !geojson.features || geojson.features.length === 0) {
        return;
    }

    state.highlightedLayer = L.geoJSON(geojson, {
        style: function (feature) {
            return {
                color: '#22d3ee',
                weight: 5,
                opacity: 0.95,
                dashArray: '',
                lineCap: 'round',
                lineJoin: 'round'
            };
        },
        onEachFeature: function (feature, layer) {
            layer.on('click', (e) => {
                L.DomEvent.stopPropagation(e);
                displaySectionDetails(feature.properties);
            });
        }
    }).addTo(map);

    // Fit map bounds to highlighted features
    map.fitBounds(state.highlightedLayer.getBounds(), { padding: [40, 40] });
}

/**
 * Show section properties in Tab 3 (Szakasz Info)
 */
function displaySectionDetails(properties) {
    document.getElementById('no-info-selected').classList.add('hidden');
    const details = document.getElementById('info-details');
    details.classList.remove('hidden');

    // Populate data
    document.getElementById('info-route-id').textContent = properties.utvonal_id || 'Nincs ID';
    document.getElementById('info-notes').textContent = properties.notes || properties.okkchange_name || 'Nincs kiegészítő megjegyzés ehhez a szakaszhoz.';
    
    // Badge
    const badge = document.getElementById('info-badge');
    badge.textContent = properties.signs || '?';
    badge.className = 'trail-badge'; // Reset classes
    if (properties.signs) {
        if (properties.signs.includes('K')) badge.classList.add('bg-blue');
        else if (properties.signs.includes('P')) badge.classList.add('bg-red');
        else if (properties.signs.includes('S')) badge.classList.add('bg-yellow', 'text-dark');
        else if (properties.signs.includes('Z')) badge.classList.add('bg-green');
    }

    // Attributes
    document.getElementById('info-road-type').textContent = roadTypes[properties.roadtype] || 'Ismeretlen';
    document.getElementById('info-surf-type').textContent = surfTypes[properties.surftype] || 'Ismeretlen';
    document.getElementById('info-length').textContent = properties.length3d ? `${Math.round(properties.length3d)} m` : '--';
    document.getElementById('info-gain').textContent = properties.emelkedes ? `${properties.emelkedes.toFixed(1)} m` : '0 m';
    document.getElementById('info-loss').textContent = properties.lejtes ? `${properties.lejtes.toFixed(1)} m` : '0 m';
    document.getElementById('info-time-oda').textContent = properties.menetido_oda ? `${Math.round(properties.menetido_oda)} perc` : '--';
    document.getElementById('info-time-vissza').textContent = properties.menetido_vissza ? `${Math.round(properties.menetido_vissza)} perc` : '--';
    document.getElementById('info-paint-year').textContent = properties.festes_eve || 'N/A';
    document.getElementById('info-surveyor').textContent = properties.surveyor || 'N/A';

    // Switch to info tab
    switchTab('tab-info');
}

/**
 * Handle clicks on map to identify closest trail when NOT in planning mode
 */
map.on('click', async (e) => {
    if (state.isPlanning) {
        addStopMarker(e.latlng);
        return;
    }

    // Spatial query to find clicked path
    const buffer = 0.001; // Approx 100 meters
    const bbox = {
        xmin: e.latlng.lng - buffer,
        ymin: e.latlng.lat - buffer,
        xmax: e.latlng.lng + buffer,
        ymax: e.latlng.lat + buffer
    };

    const result = await queryFeatureLayer(null, bbox);
    if (result && result.features && result.features.length > 0) {
        // Find closest feature
        let closestFeature = result.features[0];
        highlightFeatures(result);
        displaySectionDetails(closestFeature.properties);
    }
});

/**
 * Active signs grid filtering
 */
document.querySelectorAll('.sign-filter-btn').forEach(button => {
    button.addEventListener('click', async () => {
        const sign = button.getAttribute('data-sign');
        
        // Toggle filter
        if (state.activeSignFilter === sign) {
            state.activeSignFilter = null;
            button.classList.remove('active');
            if (state.highlightedLayer) {
                map.removeLayer(state.highlightedLayer);
                state.highlightedLayer = null;
            }
            return;
        }

        // Deactivate others
        document.querySelectorAll('.sign-filter-btn').forEach(btn => btn.classList.remove('active'));
        button.classList.add('active');
        state.activeSignFilter = sign;

        // Perform query within current viewport to avoid giant downloads
        const bounds = map.getBounds();
        const bbox = {
            xmin: bounds.getWest(),
            ymin: bounds.getSouth(),
            xmax: bounds.getEast(),
            ymax: bounds.getNorth()
        };

        const result = await queryFeatureLayer(`signs LIKE '%${sign}%'`, bbox);
        if (result) {
            highlightFeatures(result);
        }
    });
});

/**
 * Search by Route ID
 */
document.getElementById('btn-search-id').addEventListener('click', performRouteIdSearch);
document.getElementById('route-search-id').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') performRouteIdSearch();
});

async function performRouteIdSearch() {
    const routeId = document.getElementById('route-search-id').value.trim();
    if (!routeId) return;

    const result = await queryFeatureLayer(`utvonal_id = '${routeId}'`);
    if (result && result.features && result.features.length > 0) {
        highlightFeatures(result);
    } else {
        alert('Nem található útvonal ezzel az azonosítóval.');
    }
}

/**
 * Toggle WMS layer visibility
 */
document.getElementById('toggle-wms-layer').addEventListener('change', (e) => {
    if (e.target.checked) {
        state.wmsLayer.addTo(map);
    } else {
        map.removeLayer(state.wmsLayer);
    }
});

/**
 * Theme Toggler
 */
document.getElementById('btn-theme-toggle').addEventListener('click', () => {
    const body = document.body;
    const icon = document.querySelector('#btn-theme-toggle i');
    
    if (state.theme === 'dark') {
        state.theme = 'light';
        body.classList.remove('dark-theme');
        body.classList.add('light-theme');
        map.removeLayer(basemaps.dark);
        basemaps.light.addTo(map);
        icon.setAttribute('data-lucide', 'moon');
    } else {
        state.theme = 'dark';
        body.classList.remove('light-theme');
        body.classList.add('dark-theme');
        map.removeLayer(basemaps.light);
        basemaps.dark.addTo(map);
        icon.setAttribute('data-lucide', 'sun');
    }
    lucide.createIcons();
});

/**
 * Self Location finder
 */
document.getElementById('btn-locate').addEventListener('click', () => {
    map.locate({ setView: true, maxZoom: 14 });
});

map.on('locationfound', (e) => {
    L.circle(e.latlng, e.accuracy).addTo(map);
    L.marker(e.latlng).addTo(map).bindPopup('Itt vagy most').openPopup();
});

map.on('locationerror', (e) => {
    alert('Nem sikerült bemérni a pozíciódat: ' + e.message);
});

/**
 * Sidebar Tab Switching
 */
function switchTab(tabId) {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        if (btn.getAttribute('data-tab') === tabId) btn.classList.add('active');
        else btn.classList.remove('active');
    });
    
    document.querySelectorAll('.tab-pane').forEach(pane => {
        if (pane.id === tabId) pane.classList.add('active');
        else pane.classList.remove('active');
    });
}

document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        switchTab(btn.getAttribute('data-tab'));
    });
});

/**
 * ROUTE PLANNER LOGIC
 */
const btnStartPlanning = document.getElementById('btn-start-planning');
const btnClearRoute = document.getElementById('btn-clear-route');
const btnSolveRoute = document.getElementById('btn-solve-route');
const stopsContainer = document.getElementById('stops-list-container');
const stopsList = document.getElementById('stops-list');
const routeResults = document.getElementById('route-results');

btnStartPlanning.addEventListener('click', () => {
    if (!state.isPlanning) {
        state.isPlanning = true;
        btnStartPlanning.innerHTML = '<i data-lucide="x-circle"></i> Tervezés leállítása';
        btnStartPlanning.className = 'btn-action danger';
        stopsContainer.classList.remove('hidden');
        btnClearRoute.disabled = false;
        lucide.createIcons();
    } else {
        state.isPlanning = false;
        btnStartPlanning.innerHTML = '<i data-lucide="plus-circle"></i> Tervezés indítása';
        btnStartPlanning.className = 'btn-action green-glow';
        lucide.createIcons();
    }
});

btnClearRoute.addEventListener('click', () => {
    clearRoutePlanner();
});

function clearRoutePlanner() {
    stopsGroup.clearLayers();
    state.stops = [];
    if (state.plannedRoute) {
        map.removeLayer(state.plannedRoute);
        state.plannedRoute = null;
    }
    state.plannedCoordinates = null;
    state.plannedMetrics = null;
    stopsList.innerHTML = '';
    btnSolveRoute.disabled = true;
    routeResults.classList.add('hidden');
    btnClearRoute.disabled = true;
    
    if (state.isPlanning) {
        state.isPlanning = false;
        btnStartPlanning.innerHTML = '<i data-lucide="plus-circle"></i> Tervezés indítása';
        btnStartPlanning.className = 'btn-action green-glow';
        lucide.createIcons();
    }
    stopsContainer.classList.add('hidden');
}

function addStopMarker(latlng) {
    const index = state.stops.length + 1;
    
    // Custom numbered icon
    const icon = L.divIcon({
        className: 'stop-map-icon',
        html: `<div class="stop-index" style="transform: scale(1.2); box-shadow: 0 0 10px rgba(0,0,0,0.5);">${index}</div>`,
        iconSize: [24, 24],
        iconAnchor: [12, 12]
    });

    const marker = L.marker(latlng, { icon: icon, draggable: true }).addTo(stopsGroup);
    state.stops.push(marker);

    // Update list UI
    updateStopsListUI();

    marker.on('dragend', () => {
        updateStopsListUI();
    });

    if (state.stops.length >= 2) {
        btnSolveRoute.disabled = false;
    }
}

function updateStopsListUI() {
    stopsList.innerHTML = '';
    state.stops.forEach((marker, index) => {
        const latlng = marker.getLatLng();
        const li = document.createElement('li');
        li.className = 'stop-item';
        li.innerHTML = `
            <div class="stop-details">
                <span class="stop-index">${index + 1}</span>
                <span class="stop-coords">${latlng.lat.toFixed(4)}, ${latlng.lng.toFixed(4)}</span>
            </div>
            <button class="btn-remove-stop" data-index="${index}">
                <i data-lucide="trash-2" style="width: 16px; height: 16px;"></i>
            </button>
        `;
        stopsList.appendChild(li);
    });

    // Wire up delete buttons
    document.querySelectorAll('.btn-remove-stop').forEach(button => {
        button.addEventListener('click', (e) => {
            const idx = parseInt(button.getAttribute('data-index'));
            removeStop(idx);
        });
    });

    lucide.createIcons();
}

function removeStop(index) {
    const marker = state.stops[index];
    stopsGroup.removeLayer(marker);
    state.stops.splice(index, 1);
    
    // Reset all markers indices
    stopsGroup.clearLayers();
    const tempStops = [...state.stops];
    state.stops = [];
    
    tempStops.forEach(m => {
        addStopMarker(m.getLatLng());
    });

    updateStopsListUI();

    if (state.stops.length < 2) {
        btnSolveRoute.disabled = true;
        if (state.plannedRoute) {
            map.removeLayer(state.plannedRoute);
            state.plannedRoute = null;
        }
        routeResults.classList.add('hidden');
    }
}

/**
 * Route Solving calculation via NAServer Route solve
 */
btnSolveRoute.addEventListener('click', async () => {
    if (state.stops.length < 2) return;

    btnSolveRoute.disabled = true;
    btnSolveRoute.innerHTML = '<div class="spinner" style="width:16px;height:16px;margin:0;"></div> Számítás...';

    // Format stops as stops JSON parameter
    const stopsFeatures = state.stops.map(marker => {
        return {
            geometry: {
                x: marker.getLatLng().lng,
                y: marker.getLatLng().lat,
                spatialReference: { wkid: 4326 }
            }
        };
    });

    const stopsParam = JSON.stringify({ features: stopsFeatures });
    const url = `${API.routingSolve}?stops=${encodeURIComponent(stopsParam)}&outSR=4326&f=json&returnRoutes=true`;

    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error('Solver request failed');
        const data = await response.json();

        if (data.routes && data.routes.features && data.routes.features.length > 0) {
            const routeFeature = data.routes.features[0];
            const attributes = routeFeature.attributes;
            const geometry = routeFeature.geometry;

            // Geometry format returned: paths: [[[x1, y1], [x2, y2], ...]]
            const pathCoordinates = geometry.paths[0]; // array of [lon, lat]
            
            // Map paths to Leaflet latlng format [lat, lon]
            const leafletCoords = pathCoordinates.map(([lon, lat]) => [lat, lon]);

            // Draw route on map
            if (state.plannedRoute) {
                map.removeLayer(state.plannedRoute);
            }

            state.plannedRoute = L.polyline(leafletCoords, {
                color: '#10b981', // glowing green
                weight: 6,
                opacity: 0.9,
                lineCap: 'round',
                lineJoin: 'round',
                className: 'route-line-glow'
            }).addTo(map);

            // Fit map view to route
            map.fitBounds(state.plannedRoute.getBounds(), { padding: [50, 50] });

            // Store coordinates for GPX export
            state.plannedCoordinates = pathCoordinates;

            // Store metrics
            state.plannedMetrics = {
                length: attributes.Total_Length || attributes.Shape_Length || 0,
                time: attributes.Total_Walking_Time_3D || 0,
                gain: attributes.Total_Elevation_Gain || 0,
                loss: attributes.Total_Elevation_Loss || 0
            };

            // Display metrics in Sidebar
            displayRouteMetrics(state.plannedMetrics);

        } else {
            alert('Sikertelen útvonaltervezés. Győződj meg róla, hogy a pontok közel vannak a turistautakhoz.');
        }

    } catch (err) {
        console.error('Error during routing solve:', err);
        alert('Hiba történt az útvonal kiszámítása közben.');
    } finally {
        btnSolveRoute.disabled = false;
        btnSolveRoute.innerHTML = '<i data-lucide="refresh-cw"></i> Útvonal számítása';
        lucide.createIcons();
    }
});

function displayRouteMetrics(metrics) {
    routeResults.classList.remove('hidden');
    document.getElementById('metric-dist').textContent = `${(metrics.length / 1000).toFixed(2)} km`;
    
    // Time rendering in hours/mins
    const totalMinutes = Math.round(metrics.time);
    if (totalMinutes >= 60) {
        const hours = Math.floor(totalMinutes / 60);
        const mins = totalMinutes % 60;
        document.getElementById('metric-time').textContent = `${hours} óra ${mins} perc`;
    } else {
        document.getElementById('metric-time').textContent = `${totalMinutes} perc`;
    }

    document.getElementById('metric-gain').textContent = `${Math.round(metrics.gain)} m`;
    document.getElementById('metric-loss').textContent = `${Math.round(metrics.loss)} m`;
}

/**
 * GPX File Export trigger
 */
document.getElementById('btn-export-gpx').addEventListener('click', () => {
    if (state.plannedCoordinates && state.plannedMetrics) {
        GPXExporter.export(state.plannedCoordinates, state.plannedMetrics);
    }
});

// UI status updates helper
function showApiStatus(isAvailable, text = '') {
    const pulse = document.querySelector('.pulse-dot');
    const statusText = document.getElementById('api-status-text');
    if (isAvailable) {
        pulse.style.backgroundColor = 'var(--accent-success)';
        statusText.textContent = text || 'ArcGIS REST API elérhető';
    } else {
        pulse.style.backgroundColor = 'var(--accent-danger)';
        statusText.textContent = text || 'Szerver kapcsolat hiba';
    }
}
