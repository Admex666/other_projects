import csv
import json
import os

csv_path = "scraped_salons.csv"
html_path = "map.html"

salons = []
if os.path.exists(csv_path):
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader, None)
        if headers:
            # Find indices
            name_idx = headers.index("Név") if "Név" in headers else 0
            link_idx = headers.index("Google Maps Link") if "Google Maps Link" in headers else 1
            lat_idx = headers.index("Szélességi fok") if "Szélességi fok" in headers else 2
            lng_idx = headers.index("Hosszúsági fok") if "Hosszúsági fok" in headers else 3
            web_idx = headers.index("Weboldal") if "Weboldal" in headers else 4
            phone_idx = headers.index("Telefon") if "Telefon" in headers else 5
            addr_idx = headers.index("Cím") if "Cím" in headers else 6
            email_idx = headers.index("E-mail") if "E-mail" in headers else 7
            
            for row in reader:
                if len(row) > max(name_idx, link_idx, lat_idx, lng_idx, web_idx, phone_idx, addr_idx, email_idx):
                    lat_str = row[lat_idx].strip()
                    lng_str = row[lng_idx].strip()
                    if lat_str and lng_str:
                        try:
                            salons.append({
                                "name": row[name_idx].strip(),
                                "link": row[link_idx].strip(),
                                "lat": float(lat_str),
                                "lng": float(lng_str),
                                "website": row[web_idx].strip(),
                                "phone": row[phone_idx].strip(),
                                "address": row[addr_idx].strip(),
                                "email": row[email_idx].strip()
                            })
                        except ValueError:
                            pass

salons_json = json.dumps(salons, ensure_ascii=False, indent=2)

html_content = f"""<!DOCTYPE html>
<html lang="hu">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ZenSlot Salon Map</title>
    <!-- Leaflet CSS -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin=""/>
    <!-- Google Fonts (Outfit & Inter) -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
    
    <style>
        :root {{
            --bg-dark: #0a0e17;
            --panel-bg: rgba(18, 26, 43, 0.7);
            --border-color: rgba(255, 255, 255, 0.1);
            --accent-gold: #e5c158;
            --accent-gold-hover: #f1d77a;
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-dark);
            color: var(--text-main);
            height: 100vh;
            display: flex;
            overflow: hidden;
        }}

        /* Side Panel */
        #sidebar {{
            width: 380px;
            background-color: #0c121f;
            border-right: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
            height: 100%;
            z-index: 10;
            box-shadow: 10px 0 30px rgba(0, 0, 0, 0.5);
        }}

        .header {{
            padding: 24px;
            border-bottom: 1px solid var(--border-color);
            background: linear-gradient(135deg, #121b2d 0%, #0c121f 100%);
        }}

        .header h1 {{
            font-family: 'Outfit', sans-serif;
            font-size: 24px;
            font-weight: 800;
            color: #ffffff;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .header h1 span {{
            color: var(--accent-gold);
        }}

        .subtitle {{
            font-size: 12px;
            color: var(--text-muted);
            margin-top: 4px;
            text-transform: uppercase;
            letter-spacing: 1.5px;
        }}

        /* Search Box */
        .search-container {{
            padding: 16px 24px;
            border-bottom: 1px solid var(--border-color);
        }}

        .search-input {{
            width: 100%;
            padding: 12px 16px;
            border-radius: 8px;
            background-color: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-color);
            color: #ffffff;
            font-size: 14px;
            outline: none;
            transition: all 0.3s ease;
        }}

        .search-input:focus {{
            border-color: var(--accent-gold);
            box-shadow: 0 0 10px rgba(229, 193, 88, 0.2);
            background-color: rgba(255, 255, 255, 0.08);
        }}

        /* Salon List */
        .salon-list {{
            flex: 1;
            overflow-y: auto;
            padding: 16px 24px;
        }}

        .salon-list::-webkit-scrollbar {{
            width: 6px;
        }}

        .salon-list::-webkit-scrollbar-thumb {{
            background-color: rgba(255, 255, 255, 0.1);
            border-radius: 3px;
        }}

        .salon-item {{
            padding: 16px;
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            margin-bottom: 12px;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }}

        .salon-item:hover {{
            background: rgba(229, 193, 88, 0.05);
            border-color: rgba(229, 193, 88, 0.3);
            transform: translateY(-2px);
        }}

        .salon-item.active {{
            background: rgba(229, 193, 88, 0.1);
            border-color: var(--accent-gold);
            box-shadow: 0 4px 20px rgba(229, 193, 88, 0.15);
        }}

        .salon-item-name {{
            font-family: 'Outfit', sans-serif;
            font-size: 16px;
            font-weight: 600;
            color: #ffffff;
            margin-bottom: 6px;
        }}

        .salon-item-address {{
            font-size: 12px;
            color: var(--text-muted);
            display: flex;
            align-items: center;
            gap: 6px;
        }}

        .salon-item-contact {{
            font-size: 11px;
            color: var(--accent-gold);
            margin-top: 8px;
            display: flex;
            gap: 12px;
        }}

        /* Map Container */
        #map {{
            flex: 1;
            height: 100%;
        }}

        /* Leaflet Overrides for Dark Mode */
        .leaflet-container {{
            background-color: var(--bg-dark) !important;
        }}

        .leaflet-bar a {{
            background-color: #121b2d !important;
            color: #ffffff !important;
            border-bottom: 1px solid var(--border-color) !important;
            transition: all 0.2s ease;
        }}

        .leaflet-bar a:hover {{
            background-color: var(--accent-gold) !important;
            color: var(--bg-dark) !important;
        }}

        /* Popups */
        .leaflet-popup-content-wrapper {{
            background: rgba(12, 18, 31, 0.95) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 12px !important;
            color: var(--text-main) !important;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5) !important;
            backdrop-filter: blur(10px);
        }}

        .leaflet-popup-tip {{
            background: rgba(12, 18, 31, 0.95) !important;
            border: 1px solid var(--border-color) !important;
        }}

        .popup-container {{
            font-family: 'Inter', sans-serif;
            padding: 4px;
        }}

        .popup-title {{
            font-family: 'Outfit', sans-serif;
            font-size: 16px;
            font-weight: 800;
            color: #ffffff;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding-bottom: 8px;
            margin-bottom: 8px;
        }}

        .popup-row {{
            margin-bottom: 6px;
            font-size: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .popup-label {{
            color: var(--text-muted);
            min-width: 60px;
        }}

        .popup-value {{
            color: var(--text-main);
            font-weight: 500;
        }}

        .popup-value a {{
            color: var(--accent-gold);
            text-decoration: none;
            transition: color 0.2s;
        }}

        .popup-value a:hover {{
            color: var(--accent-gold-hover);
            text-decoration: underline;
        }}

        /* Custom Marker */
        .custom-marker {{
            width: 32px;
            height: 32px;
            background-color: var(--accent-gold);
            border: 2px solid #ffffff;
            border-radius: 50% 50% 50% 0;
            transform: rotate(-45deg);
            margin-left: -16px;
            margin-top: -32px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 10px rgba(0,0,0,0.5);
            transition: all 0.3s ease;
        }}
        
        .custom-marker::after {{
            content: '';
            width: 10px;
            height: 10px;
            background-color: #0c121f;
            border-radius: 50%;
        }}

        .custom-marker.active {{
            background-color: #ffffff;
            border-color: var(--accent-gold);
            transform: rotate(-45deg) scale(1.2);
            box-shadow: 0 0 20px var(--accent-gold);
        }}
        
        .custom-marker.active::after {{
            background-color: var(--accent-gold);
        }}
    </style>
</head>
<body>

    <div id="sidebar">
        <div class="header">
            <h1>Zen<span>Slot</span> Maps</h1>
            <div class="subtitle">B2B Lead Térkép ({len(salons)} partner)</div>
        </div>
        
        <div class="search-container">
            <input type="text" id="search" class="search-input" placeholder="Keresés név vagy cím alapján...">
        </div>
        
        <div class="salon-list" id="salonList">
            <!-- Items generated dynamically -->
        </div>
    </div>

    <div id="map"></div>

    <!-- Leaflet JS -->
    <script href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

    <script>
        // Salon adatok
        const salons = {salons_json};

        // Térkép inicializálása Budapestre fókuszálva
        const map = L.map('map', {{
            zoomControl: true
        }}).setView([47.4979, 19.0402], 13);

        // Sötét térkép stílus (CartoDB Dark Matter)
        L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
            subdomains: 'abcd',
            maxZoom: 20
        }}).addTo(map);

        const markers = [];
        const markerGroup = L.featureGroup().addTo(map);

        // Szalonok kirajzolása és lista feltöltése
        function renderSalons(filterText = '') {{
            const listContainer = document.getElementById('salonList');
            listContainer.innerHTML = '';
            
            // Meglévő markerek törlése a térképről
            markerGroup.clearLayers();
            markers.length = 0;

            const query = filterText.toLowerCase().trim();

            salons.forEach((salon, index) => {{
                if (query && !salon.name.toLowerCase().includes(query) && !salon.address.toLowerCase().includes(query)) {{
                    return;
                }}

                // Egyedi HTML marker létrehozása
                const icon = L.divIcon({{
                    className: 'custom-marker-container',
                    html: `<div class="custom-marker" id="marker-${{index}}"></div>`,
                    iconSize: [32, 32],
                    iconAnchor: [16, 32]
                }});

                // Marker elhelyezése a térképen
                const marker = L.marker([salon.lat, salon.lng], {{ icon: icon }});
                
                // Popup tartalom
                const popupContent = `
                    <div class="popup-container">
                        <div class="popup-title">${{salon.name}}</div>
                        <div class="popup-row">
                            <span class="popup-label">Cím:</span>
                            <span class="popup-value">${{salon.address || 'Nincs megadva'}}</span>
                        </div>
                        <div class="popup-row">
                            <span class="popup-label">Telefon:</span>
                            <span class="popup-value">${{salon.phone || 'Nincs megadva'}}</span>
                        </div>
                        <div class="popup-row">
                            <span class="popup-label">E-mail:</span>
                            <span class="popup-value">${{salon.email ? `<a href="mailto:${{salon.email}}">${{salon.email}}</a>` : 'Nincs megadva'}}</span>
                        </div>
                        <div class="popup-row">
                            <span class="popup-label">Weboldal:</span>
                            <span class="popup-value">${{salon.website ? `<a href="${{salon.website}}" target="_blank">${{salon.website.replace('https://', '').replace('http://', '').split('/')[0]}}</a>` : 'Nincs megadva'}}</span>
                        </div>
                        <div class="popup-row" style="margin-top: 10px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 8px;">
                            <span class="popup-value"><a href="${{salon.link}}" target="_blank">Megnyitás Google Maps-en &rarr;</a></span>
                        </div>
                    </div>
                `;

                marker.bindPopup(popupContent, {{
                    maxWidth: 300,
                    minWidth: 260
                }});

                markerGroup.addLayer(marker);

                // Elemek mentése referenciának
                markers.push({{
                    index: index,
                    salon: salon,
                    marker: marker
                }});

                // Lista elem generálása
                const item = document.createElement('div');
                item.className = 'salon-item';
                item.id = `item-${{index}}`;
                item.innerHTML = `
                    <div class="salon-item-name">${{salon.name}}</div>
                    <div class="salon-item-address">📍 ${{salon.address.split(',')[0] || salon.address}}</div>
                    <div class="salon-item-contact">
                        ${{salon.phone ? `📞 ${{salon.phone}}` : ''}}
                        ${{salon.email ? `✉️ ${{salon.email}}` : ''}}
                    </div>
                `;

                item.addEventListener('click', () => {{
                    selectSalon(index);
                }});

                listContainer.appendChild(item);

                // Marker click esemény
                marker.on('click', () => {{
                    selectSalon(index, false); // false = ne mozgassuk újra a térképet ha rákattintottunk a markerre
                }});
            }});

            // Térkép igazítása, hogy minden marker látsszon
            if (markers.length > 0) {{
                map.fitBounds(markerGroup.getBounds(), {{ padding: [50, 50] }});
            }}
        }}

        // Kijelölési logika
        function selectSalon(index, pan = true) {{
            // Elemek aktív állapotának törlése
            document.querySelectorAll('.salon-item').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.custom-marker').forEach(el => el.classList.remove('active'));

            const selected = markers.find(m => m.index === index);
            if (selected) {{
                // Lista elem kiemelése
                const item = document.getElementById(`item-${{index}}`);
                if (item) {{
                    item.classList.add('active');
                    item.scrollIntoView({{ behavior: 'smooth', block: 'nearest' }});
                }}

                // Marker kiemelése
                const markerEl = document.getElementById(`marker-${{index}}`);
                if (markerEl) {{
                    markerEl.classList.add('active');
                }}

                // Térkép mozgatása és popup megnyitása
                if (pan) {{
                    map.setView([selected.salon.lat, selected.salon.lng], 15, {{
                        animate: true,
                        duration: 1
                    }});
                }}
                
                selected.marker.openPopup();
            }}
        }}

        // Kereső mező kezelése
        document.getElementById('search').addEventListener('input', (e) => {{
            renderSalons(e.target.value);
        }});

        // Kezdeti renderelés
        renderSalons();
    </script>
</body>
</html>
"""

with open(html_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print("map.html successfully generated!")
