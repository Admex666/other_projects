const os = require('os');

/**
 * Returns the best IPv4 address of the host machine on the local network (LAN / Wi-Fi).
 * Ignores internal/loopback and prioritizes Wi-Fi/Ethernet adapters over virtual adapters.
 */
function getLanIp() {
  const nets = os.networkInterfaces();
  const candidates = [];

  for (const name of Object.keys(nets)) {
    const netList = nets[name];
    if (!netList) continue;

    for (const net of netList) {
      // Family must be IPv4, and non-internal (not 127.0.0.1)
      const family = typeof net.family === 'string' ? net.family : (net.family === 4 ? 'IPv4' : '');
      if (family === 'IPv4' && !net.internal) {
        // Score adapter relevance:
        // Wi-Fi or Ethernet or wlan or eth get higher priority
        let priority = 1;
        const lowerName = name.toLowerCase();
        if (lowerName.includes('wi-fi') || lowerName.includes('wifi') || lowerName.includes('wireless') || lowerName.includes('wlan')) {
          priority = 10;
        } else if (lowerName.includes('ethernet') || lowerName.includes('eth') || lowerName.includes('helyi')) {
          // If it's a virtual connection (e.g. "Helyi kapcsolat* 10" hotspot or vEthernet), deprioritize slightly
          if (lowerName.includes('*') || lowerName.includes('vethernet') || lowerName.includes('virtual') || lowerName.includes('vmware') || lowerName.includes('vbox')) {
            priority = 2;
          } else {
            priority = 8;
          }
        }
        candidates.push({ address: net.address, name, priority });
      }
    }
  }

  // Sort candidates by priority descending
  candidates.sort((a, b) => b.priority - a.priority);

  if (candidates.length > 0) {
    return candidates[0].address;
  }

  return '127.0.0.1';
}

if (require.main === module) {
  console.log(getLanIp());
}

module.exports = { getLanIp };
