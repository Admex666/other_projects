import { describe, it, expect, afterEach } from 'vitest';
import { getWebSocketUrl } from '../../App';

describe('getWebSocketUrl', () => {
  const originalWindow = globalThis.window;

  afterEach(() => {
    globalThis.window = originalWindow;
  });

  const mockLocation = (loc: Partial<Location>) => {
    (globalThis as any).window = {
      location: {
        protocol: 'http:',
        hostname: 'localhost',
        host: 'localhost:3001',
        port: '3001',
        pathname: '/',
        origin: 'http://localhost:3001',
        ...loc,
      } as unknown as Location,
    };
  };

  it('correctly builds wss URL for HTTPS localtunnel without port 3001', () => {
    mockLocation({
      protocol: 'https:',
      hostname: 'bear-game.loca.lt',
      host: 'bear-game.loca.lt',
      port: '',
      origin: 'https://bear-game.loca.lt',
    });

    const url = getWebSocketUrl();
    expect(url).toBe('wss://bear-game.loca.lt');
  });

  it('correctly builds ws URL for local LAN with port 3001', () => {
    mockLocation({
      protocol: 'http:',
      hostname: '192.168.1.15',
      host: '192.168.1.15:3001',
      port: '3001',
      origin: 'http://192.168.1.15:3001',
    });

    const url = getWebSocketUrl();
    expect(url).toBe('ws://192.168.1.15:3001');
  });

  it('correctly maps Vite dev server port 5173 to backend port 3001', () => {
    mockLocation({
      protocol: 'http:',
      hostname: 'localhost',
      host: 'localhost:5173',
      port: '5173',
      origin: 'http://localhost:5173',
    });

    const url = getWebSocketUrl();
    expect(url).toBe('ws://localhost:3001');
  });

  it('handles standard HTTP port 80 domain without appending 3001', () => {
    mockLocation({
      protocol: 'http:',
      hostname: 'bearnecessities.game',
      host: 'bearnecessities.game',
      port: '',
      origin: 'http://bearnecessities.game',
    });

    const url = getWebSocketUrl();
    expect(url).toBe('ws://bearnecessities.game');
  });
});

