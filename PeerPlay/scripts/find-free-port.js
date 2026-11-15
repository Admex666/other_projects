const net = require('net');

function isPortAvailable(port) {
  return new Promise((resolve) => {
    // Check with default binding (includes IPv6/dual-stack if supported)
    const server = net.createServer();

    server.once('error', (err) => {
      resolve(false);
    });

    server.once('listening', () => {
      // Also verify connecting / listening on 0.0.0.0 and 127.0.0.1
      server.close(() => {
        // Try connecting to 127.0.0.1 to double check if something else answers
        const tester = net.createConnection({ port, host: '127.0.0.1' });
        tester.once('connect', () => {
          tester.destroy();
          resolve(false); // Port is occupied!
        });
        tester.once('error', () => {
          resolve(true); // Port is actually free
        });
      });
    });

    try {
      server.listen(port);
    } catch (err) {
      resolve(false);
    }
  });
}

async function findFreePort(startPort = 3000, maxPort = 3100) {
  for (let port = startPort; port <= maxPort; port++) {
    const free = await isPortAvailable(port);
    if (free) {
      return port;
    }
  }
  throw new Error(`Nem talalhato szabad port ${startPort} es ${maxPort} kozott.`);
}

if (require.main === module) {
  const defaultPort = parseInt(process.env.START_PORT || process.argv[2] || '3000', 10);
  findFreePort(defaultPort)
    .then((port) => {
      process.stdout.write(String(port));
      process.exit(0);
    })
    .catch((err) => {
      console.error(err.message);
      process.exit(1);
    });
}

module.exports = { findFreePort, isPortAvailable };
