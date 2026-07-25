/**
 * GPX Exporter Utility
 * Converts route coordinates and metadata into a standard GPX (GPS Exchange Format) XML file.
 */
const GPXExporter = {
    /**
     * Serializes coordinates into GPX format and triggers a browser download.
     * @param {Array<[number, number]>} coordinates - Array of [longitude, latitude] coordinates.
     * @param {Object} metrics - Route metrics (length, time, gain, loss).
     * @param {string} fileName - Base name of the exported file.
     */
    export(coordinates, metrics, fileName = 'turistaut-terv') {
        if (!coordinates || coordinates.length === 0) {
            console.error('No coordinates to export');
            return;
        }

        const now = new Date().toISOString();
        const distKm = (metrics.length / 1000).toFixed(2);
        const timeMin = Math.round(metrics.time);
        
        let gpx = `<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="TuristaUt Kalandtervező" 
     xmlns="http://www.topografix.com/GPX/1/1" 
     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
     xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd">
  <metadata>
    <name>Tervezett túra - ${distKm} km</name>
    <desc>TuristaÚt Kalandtervezővel generált útvonal. Hossz: ${distKm} km, Tervezett idő: ${timeMin} perc. Emelkedés: ${Math.round(metrics.gain)}m, Lejtés: ${Math.round(metrics.loss)}m.</desc>
    <time>${now}</time>
  </metadata>
  <trk>
    <name>Tervezett túra (${distKm} km)</name>
    <type>Hike</type>
    <trkseg>
`;

        coordinates.forEach(([lon, lat]) => {
            // GPX requires lat, lon attribute structure
            gpx += `      <trkpt lat="${lat.toFixed(6)}" lon="${lon.toFixed(6)}"></trkpt>\n`;
        });

        gpx += `    </trkseg>
  </trk>
</gpx>`;

        // Create Blob and download
        const blob = new Blob([gpx], { type: 'application/gpx+xml;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        
        link.href = url;
        link.setAttribute('download', `${fileName}-${new Date().toLocaleDateString('hu-HU').replace(/\s/g, '')}.gpx`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }
};

// Export to global namespace
window.GPXExporter = GPXExporter;
