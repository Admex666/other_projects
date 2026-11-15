const fs = require('fs');
const path = require('path');
const https = require('https');
const { spawn, execFileSync } = require('child_process');
const { getLanIp } = require('./get-lan-ip');

const infoFilePath = path.join(__dirname, '..', 'public', 'tunnel-info.json');
const targetPort = parseInt(process.env.PORT || process.argv[2] || '3000', 10);
const lanIp = getLanIp();
const lanUrl = `http://${lanIp}:${targetPort}`;
const lanJoinUrl = `${lanUrl}/join`;

function findCloudflaredBinary() {
  const candidatePaths = [
    'C:\\Program Files (x86)\\cloudflared\\cloudflared.exe',
    'C:\\Program Files\\cloudflared\\cloudflared.exe',
  ];

  for (const p of candidatePaths) {
    if (fs.existsSync(p)) {
      return p;
    }
  }

  try {
    const cmd = process.platform === 'win32' ? 'where' : 'which';
    const out = execFileSync(cmd, ['cloudflared'], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] });
    const firstLine = out.split(/\r?\n/)[0].trim();
    if (firstLine) return firstLine;
  } catch {
    // Not in PATH
  }

  return null;
}

function getTunnelPassword() {
  return new Promise((resolve) => {
    const req = https.get('https://loca.lt/mytunnelpassword', { timeout: 5000 }, (res) => {
      let data = '';
      res.on('data', (chunk) => (data += chunk));
      res.on('end', () => resolve(data.trim()));
    });
    req.on('error', () => resolve(''));
    req.on('timeout', () => {
      req.destroy();
      resolve('');
    });
  });
}

function updateInfoFile(info) {
  try {
    fs.writeFileSync(infoFilePath, JSON.stringify(info, null, 2), 'utf8');
  } catch (err) {
    console.error('[HIBA] Nem sikerult a tunnel-info.json-t irni:', err.message);
  }
}

// Initial state with LAN info guaranteed available immediately
updateInfoFile({
  active: false,
  port: targetPort,
  lanIp: lanIp,
  lanUrl: lanUrl,
  lanJoinUrl: lanJoinUrl,
  url: '',
  joinUrl: lanJoinUrl,
  password: '',
  status: 'connecting',
  updatedAt: new Date().toISOString(),
});

console.log('=======================================================');
console.log('       PeerPlay Mobil Csatlakozás Vezérlő             ');
console.log('=======================================================');
console.log(`[LAN / Wi-Fi]  Garantált helyi kapcsolat elérhető:`);
console.log(`  -> Mobil Csatlakozási URL: ${lanJoinUrl}`);
console.log(`  -> (Ha a mobil ugyanazon a Wi-Fi-n van, ez azonnali és stabil!)\n`);

let currentTunnel = null;
let currentChild = null;
let isStopping = false;

const cloudflaredBin = findCloudflaredBinary();

function startCloudflaredTunnel() {
  if (isStopping) return;

  console.log(`[INTERNET TUNNEL] Cloudflare Tunnel indítása (${targetPort}-es port)...`);

  const child = spawn(cloudflaredBin, ['tunnel', '--url', `http://127.0.0.1:${targetPort}`], {
    stdio: ['ignore', 'pipe', 'pipe'],
    windowsHide: true,
  });

  currentChild = child;
  let tunnelUrlFound = false;

  const handleOutput = (chunk) => {
    const text = chunk.toString('utf8');
    if (!tunnelUrlFound) {
      const match = text.match(/https:\/\/[a-z0-9-]+\.trycloudflare\.com/i);
      if (match && match[0]) {
        tunnelUrlFound = true;
        const url = match[0];
        const info = {
          active: true,
          provider: 'cloudflare',
          port: targetPort,
          lanIp: lanIp,
          lanUrl: lanUrl,
          lanJoinUrl: lanJoinUrl,
          url: url,
          joinUrl: `${url}/join`,
          password: '',
          status: 'online',
          updatedAt: new Date().toISOString(),
        };

        updateInfoFile(info);

        console.log('\n[SIKER] A Cloudflare villámgyors internetes tunnel él!');
        console.log(`  -> Internetes URL:         ${info.joinUrl}`);
        console.log(`  -> Helyi Wi-Fi URL:        ${lanJoinUrl}`);
        console.log(`  -> (Nincs jelszó, HTTP/2 + Gzip tömörítés aktív!)\n`);
      }
    }
  };

  child.stdout.on('data', handleOutput);
  child.stderr.on('data', handleOutput);

  child.on('error', (err) => {
    console.error(`[HIBA] Cloudflare tunnel folyamat hiba (${err.message}). Fallback localtunnel-re...`);
    currentChild = null;
    if (!isStopping) {
      startLocaltunnelWithRetry();
    }
  });

  child.on('close', (code) => {
    currentChild = null;
    if (isStopping) return;
    console.warn(`[FIGYELEM] A Cloudflare tunnel leállt (kód: ${code}). Újraindítás 5 mp múlva...`);
    updateInfoFile({
      active: false,
      port: targetPort,
      lanIp: lanIp,
      lanUrl: lanUrl,
      lanJoinUrl: lanJoinUrl,
      url: '',
      joinUrl: lanJoinUrl,
      password: '',
      status: 'disconnected',
      updatedAt: new Date().toISOString(),
    });
    setTimeout(startCloudflaredTunnel, 5000);
  });
}

async function startLocaltunnelWithRetry() {
  if (isStopping) return;

  console.log(`[INTERNET TUNNEL] Kapcsolódás a localtunnel szerverhez (${targetPort}-es port)...`);
  try {
    const localtunnel = require('localtunnel');
    const password = await getTunnelPassword();
    const tunnel = await localtunnel({ port: targetPort });
    currentTunnel = tunnel;

    const info = {
      active: true,
      provider: 'localtunnel',
      port: targetPort,
      lanIp: lanIp,
      lanUrl: lanUrl,
      lanJoinUrl: lanJoinUrl,
      url: tunnel.url,
      joinUrl: `${tunnel.url}/join`,
      password: password,
      status: 'online',
      updatedAt: new Date().toISOString(),
    };

    updateInfoFile(info);

    console.log('\n[SIKER] A nyilvános internetes tunnel él!');
    console.log(`  -> Internetes URL:         ${info.joinUrl}`);
    if (password) {
      console.log(`  -> Tunnel jelszó (ha kéri): ${password}`);
    }
    console.log(`  -> Helyi Wi-Fi URL:        ${lanJoinUrl}`);
    console.log(`\nA QR kód mindkét módot támogatja a webes felületen.\n`);

    tunnel.on('close', () => {
      console.warn('[FIGYELEM] A localtunnel kapcsolat lezárult. Újrakapcsolódás 5 mp múlva...');
      updateInfoFile({
        active: false,
        port: targetPort,
        lanIp: lanIp,
        lanUrl: lanUrl,
        lanJoinUrl: lanJoinUrl,
        url: '',
        joinUrl: lanJoinUrl,
        password: '',
        status: 'disconnected',
        updatedAt: new Date().toISOString(),
      });
      if (!isStopping) {
        setTimeout(startLocaltunnelWithRetry, 5000);
      }
    });

    tunnel.on('error', (err) => {
      console.error('[HIBA] Tunnel hiba:', err.message);
      tunnel.close();
    });
  } catch (err) {
    console.error(`[HIBA] Nem sikerült a localtunnelt felépíteni (${err.message}). Újrapróbálás 6 mp múlva...`);
    updateInfoFile({
      active: false,
      port: targetPort,
      lanIp: lanIp,
      lanUrl: lanUrl,
      lanJoinUrl: lanJoinUrl,
      url: '',
      joinUrl: lanJoinUrl,
      password: '',
      status: 'error',
      errorMessage: err.message,
      updatedAt: new Date().toISOString(),
    });
    if (!isStopping) {
      setTimeout(startLocaltunnelWithRetry, 6000);
    }
  }
}

function startTunnelWithRetry() {
  if (cloudflaredBin) {
    startCloudflaredTunnel();
  } else {
    startLocaltunnelWithRetry();
  }
}

process.on('SIGINT', () => {
  isStopping = true;
  console.log('\n[INFO] Kilépés...');
  if (currentChild) {
    try {
      currentChild.kill();
    } catch (e) {}
  }
  if (currentTunnel) {
    try {
      currentTunnel.close();
    } catch (e) {}
  }
  process.exit(0);
});

startTunnelWithRetry();
