import http from 'http';
import fs from 'fs';
import os from 'os';
import path from 'path';
import { fileURLToPath } from 'url';
import { WebSocketServer, WebSocket } from 'ws';
import { RoomManager } from './roomManager';
import type { ClientMessage } from './protocol';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function getLanIp(): string {
  const interfaces = os.networkInterfaces();
  for (const name of Object.keys(interfaces)) {
    for (const iface of interfaces[name] || []) {
      if (iface.family === 'IPv4' && !iface.internal && !iface.address.startsWith('169.254.')) {
        return iface.address;
      }
    }
  }
  return 'localhost';
}

const PORT = process.env.PORT ? parseInt(process.env.PORT, 10) : 3001;
const LAN_IP = getLanIp();
const HOST = process.env.HOST || LAN_IP;
const BASE_URL = process.env.BASE_URL || `http://${HOST}:${PORT}`;

export const roomManager = new RoomManager(BASE_URL);

// MIME type map for static serving
const MIME_TYPES: Record<string, string> = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif': 'image/gif',
  '.svg': 'image/svg+xml',
  '.webp': 'image/webp',
  '.ico': 'image/x-icon',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
};

const DIST_DIR = path.resolve(__dirname, '../../dist');

export const server = http.createServer((req, res) => {
  const url = new URL(req.url || '/', `http://${req.headers.host || 'localhost'}`);
  const pathname = decodeURIComponent(url.pathname);

  // Health and info API routes
  if (pathname === '/health' || pathname === '/api/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(
      JSON.stringify({
        status: 'ok',
        name: 'Bear Necessities Game Server',
        activeRooms: roomManager.getAllRooms().length,
      })
    );
    return;
  }

  if (pathname === '/api/network-info') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(
      JSON.stringify({
        lanIp: LAN_IP,
        port: PORT,
        baseUrl: BASE_URL,
      })
    );
    return;
  }

  // Room status API
  if (pathname.startsWith('/api/rooms/')) {
    const roomId = pathname.replace('/api/rooms/', '').toUpperCase();
    const room = roomManager.getRoom(roomId);
    if (!room) {
      res.writeHead(404, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Room not found' }));
      return;
    }

    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(
      JSON.stringify({
        roomId: room.roomId,
        players: Object.values(room.players).map(p => ({
          id: p.id,
          name: p.name,
          connected: p.connected,
        })),
        hasGame: Boolean(room.gameState),
        status: room.gameState ? room.gameState.status : 'waiting',
      })
    );
    return;
  }

  // Serve static files if dist folder exists
  if (fs.existsSync(DIST_DIR)) {
    let filePath = path.join(DIST_DIR, pathname === '/' ? 'index.html' : pathname);

    // Security check to avoid path traversal
    if (!filePath.startsWith(DIST_DIR)) {
      res.writeHead(403);
      res.end('Forbidden');
      return;
    }

    if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
      const ext = path.extname(filePath).toLowerCase();
      const contentType = MIME_TYPES[ext] || 'application/octet-stream';
      res.writeHead(200, { 'Content-Type': contentType });
      fs.createReadStream(filePath).pipe(res);
      return;
    }

    // SPA fallback: return index.html for client-side routing
    const indexPath = path.join(DIST_DIR, 'index.html');
    if (fs.existsSync(indexPath)) {
      res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
      fs.createReadStream(indexPath).pipe(res);
      return;
    }
  }

  // Standalone mode default response
  res.writeHead(200, { 'Content-Type': 'application/json' });
  res.end(
    JSON.stringify({
      status: 'ok',
      name: 'Bear Necessities Game Server',
      message: 'Connect via WebSocket to play Bear Necessities multiplayer.',
    })
  );
});

export const wss = new WebSocketServer({ server });

wss.on('connection', (ws: WebSocket) => {
  ws.on('message', (rawMessage: Buffer | string) => {
    try {
      const data = JSON.parse(rawMessage.toString()) as ClientMessage;

      switch (data.type) {
        case 'CREATE_ROOM': {
          try {
            const roomResult = roomManager.createRoom(data.playerName);
            roomManager.bindSocket(ws, roomResult.roomId, roomResult.playerId);
            ws.send(
              JSON.stringify({
                type: 'ROOM_CREATED',
                roomId: roomResult.roomId,
                playerId: roomResult.playerId,
                sessionToken: roomResult.sessionToken,
                inviteUrl: roomResult.inviteUrl,
              })
            );
          } catch (err: any) {
            ws.send(JSON.stringify({ type: 'ERROR', code: 'CREATE_ROOM_FAILED', message: err.message }));
          }
          break;
        }

        case 'JOIN_ROOM': {
          try {
            const joinResult = roomManager.joinRoom(data.roomId, data.playerName);
            roomManager.bindSocket(ws, joinResult.roomId, joinResult.playerId);
            ws.send(
              JSON.stringify({
                type: 'ROOM_JOINED',
                roomId: joinResult.roomId,
                playerId: joinResult.playerId,
                sessionToken: joinResult.sessionToken,
              })
            );

            // Game begins when 2nd player joins: notify both players
            roomManager.broadcastGameStarted(joinResult.roomId);
          } catch (err: any) {
            ws.send(JSON.stringify({ type: 'ERROR', code: 'JOIN_ROOM_FAILED', message: err.message }));
          }
          break;
        }

        case 'RECONNECT': {
          const recon = roomManager.reconnectPlayer(data.roomId, data.playerId, data.sessionToken, ws);
          if (recon.success && recon.state) {
            ws.send(
              JSON.stringify({
                type: 'STATE_UPDATE',
                roomId: data.roomId,
                state: recon.state,
                reason: 'RECONNECTED',
              })
            );
          } else {
            ws.send(
              JSON.stringify({
                type: 'ERROR',
                code: 'RECONNECT_FAILED',
                message: recon.error || 'Failed to reconnect.',
              })
            );
          }
          break;
        }

        case 'SUBMIT_SELECTION':
        case 'CONFIRM_PLACEMENT':
        case 'CHOOSE_REFILL_OPTION': {
          const actionResult = roomManager.handleAction(data.roomId, data.playerId, data);
          if (!actionResult.success) {
            ws.send(
              JSON.stringify({
                type: 'ERROR',
                code: 'INVALID_ACTION',
                message: actionResult.error || 'Action could not be executed.',
              })
            );
          }
          break;
        }

        case 'REQUEST_REMATCH': {
          const rematchResult = roomManager.handleRematch(data.roomId, data.playerId);
          if (!rematchResult.success) {
            ws.send(
              JSON.stringify({
                type: 'ERROR',
                code: 'REMATCH_FAILED',
                message: rematchResult.error || 'Rematch request failed.',
              })
            );
          }
          break;
        }

        case 'READY_NEXT_ROUND': {
          const readyResult = roomManager.handleReadyNextRound(data.roomId, data.playerId);
          if (!readyResult.success) {
            ws.send(
              JSON.stringify({
                type: 'ERROR',
                code: 'READY_NEXT_ROUND_FAILED',
                message: readyResult.error || 'Ready next round failed.',
              })
            );
          }
          break;
        }

        case 'GAME_ACTION': {
          const actionResult = roomManager.handleAction(data.roomId, data.playerId, data.action);
          if (!actionResult.success) {
            ws.send(
              JSON.stringify({
                type: 'ERROR',
                code: 'INVALID_ACTION',
                message: actionResult.error || 'Game action could not be executed.',
              })
            );
          }
          break;
        }

        default:
          ws.send(
            JSON.stringify({
              type: 'ERROR',
              code: 'UNKNOWN_MESSAGE_TYPE',
              message: `Unknown message type: ${(data as any).type}`,
            })
          );
      }
    } catch {
      ws.send(
        JSON.stringify({
          type: 'ERROR',
          code: 'INVALID_JSON',
          message: 'Received invalid JSON payload.',
        })
      );
    }
  });

  ws.on('close', () => {
    roomManager.handleDisconnect(ws);
  });

  ws.on('error', () => {
    roomManager.handleDisconnect(ws);
  });
});

if (process.env.NODE_ENV !== 'test') {
  server.listen(PORT, () => {
    console.log(`Bear Necessities server running on port ${PORT}`);
  });
}
