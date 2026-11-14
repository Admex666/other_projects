const localtunnel = require('localtunnel');
const fs = require('fs');
const path = require('path');
const https = require('https');

const infoFilePath = path.join(__dirname, '..', 'public', 'tunnel-info.json');

function getTunnelPassword() {
  return new Promise((resolve) => {
    const req = https.get('https://loca.lt/mytunnelpassword', { timeout: 5000 }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve(data.trim()));
    });
    req.on('error', () => resolve(''));
    req.on('timeout', () => { req.destroy(); resolve(''); });
  });
}

(async () => {
  console.log('=======================================================');
  console.log('       PeerPlay Mobil Tunnel - Localtunnel');
  console.log('=======================================================');
  console.log('[INFO] Tunnel letrehozasa a 3000-es portra...');

  try {
    const password = await getTunnelPassword();
    const tunnel = await localtunnel({ port: 3000 });

    const info = {
      active: true,
      url: tunnel.url,
      joinUrl: `${tunnel.url}/join`,
      password: password,
      updatedAt: new Date().toISOString()
    };

    fs.writeFileSync(infoFilePath, JSON.stringify(info, null, 2), 'utf8');

    console.log('\n[SIKER] A nyilvanos tunnel elerheto!');
    console.log(`- Mobil Csatlakozasi URL:  ${info.joinUrl}`);
    if (password) {
      console.log(`- Tunnel Jelszo (ha keri): ${password}`);
    }
    console.log('\nA QR kod es a link automatikusan megjelent a http://localhost:3000 fooldalon.\n');
    console.log('Tartsd nyitva ezt az ablakot a teszteles alatt!\n');

    tunnel.on('close', () => {
      console.log('[INFO] A tunnel lezart.');
      try {
        fs.writeFileSync(infoFilePath, JSON.stringify({ active: false }, null, 2), 'utf8');
      } catch (e) {}
    });

    tunnel.on('error', (err) => {
      console.error('[HIBA] Tunnel hiba:', err.message);
    });

  } catch (err) {
    console.error('[HIBA] Nem sikerult a tunnelt letrehozni:', err.message);
  }
})();
