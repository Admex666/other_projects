import { describe, it, expect, beforeEach, vi } from 'vitest';
import { RoomManager } from '../roomManager';
import { filterStateForPlayer } from '../protocol';
import type { GameState } from '../../game/types';

describe('RoomManager & Multiplayer Server Protocol', () => {
  let roomManager: RoomManager;

  beforeEach(() => {
    roomManager = new RoomManager('http://localhost:3001');
  });

  describe('Room Creation & Joining', () => {
    it('creates a room with a 6-character uppercase alphanumeric code and host session', () => {
      const room = roomManager.createRoom('Alice');

      expect(room.roomId).toMatch(/^[A-Z0-9]{6}$/);
      expect(room.playerId).toMatch(/^p_/);
      expect(room.sessionToken).toMatch(/^tok_/);
      expect(room.inviteUrl).toBe(`http://localhost:3001/?room=${room.roomId}`);

      const stored = roomManager.getRoom(room.roomId);
      expect(stored).toBeDefined();
      expect(stored?.players[room.playerId].name).toBe('Alice');
      expect(stored?.gameState).toBeNull(); // Not started yet until 2nd player joins
    });

    it('rejects empty host name', () => {
      expect(() => roomManager.createRoom('')).toThrow('Host player name cannot be empty.');
      expect(() => roomManager.createRoom('   ')).toThrow('Host player name cannot be empty.');
    });

    it('allows a 2nd player to join and initializes the game automatically', () => {
      const host = roomManager.createRoom('Alice');
      const guest = roomManager.joinRoom(host.roomId, 'Bob');

      expect(guest.roomId).toBe(host.roomId);
      expect(guest.playerId).toMatch(/^p_/);
      expect(guest.playerId).not.toBe(host.playerId);
      expect(guest.sessionToken).toMatch(/^tok_/);

      const room = roomManager.getRoom(host.roomId);
      expect(room?.gameState).toBeDefined();
      expect(room?.gameState?.status).toBe('in_progress');
      expect(room?.gameState?.round).toBe(1);
      expect(room?.gameState?.phase).toBe('DRAFT');

      const players = room!.gameState!.players;
      expect(players[host.playerId].hand.length).toBe(5);
      expect(players[guest.playerId].hand.length).toBe(5);
    });

    it('rejects joining a non-existent room', () => {
      expect(() => roomManager.joinRoom('NONEXIST', 'Charlie')).toThrow('not found');
    });

    it('rejects a 3rd player trying to join an already full room', () => {
      const host = roomManager.createRoom('Alice');
      roomManager.joinRoom(host.roomId, 'Bob');

      expect(() => roomManager.joinRoom(host.roomId, 'Charlie')).toThrow('already full');
    });
  });

  describe('Authoritative State Filtering (filterStateForPlayer)', () => {
    let host: ReturnType<typeof roomManager.createRoom>;
    let guest: ReturnType<typeof roomManager.joinRoom>;
    let gameState: GameState;

    beforeEach(() => {
      host = roomManager.createRoom('Alice');
      guest = roomManager.joinRoom(host.roomId, 'Bob');
      gameState = roomManager.getRoom(host.roomId)!.gameState!;
    });

    it('reveals own hand and reserveCard to Player 1, but masks Player 2 cards', () => {
      // Give guest an active reserve card for testing
      gameState.players[guest.playerId].reserveCard = { ...gameState.players[guest.playerId].hand[0] };

      const filteredForHost = filterStateForPlayer(gameState, host.playerId);

      // Host sees their own cards fully
      expect(filteredForHost.players[host.playerId].hand[0].id).toBeGreaterThan(0);
      expect(filteredForHost.players[host.playerId].hand[0].name).not.toBe('Hidden Card');

      // Host sees Bob's hand masked
      const bobHand = filteredForHost.players[guest.playerId].hand;
      expect(bobHand.length).toBe(5);
      for (const card of bobHand) {
        expect(card.id).toBe(-1);
        expect(card.name).toBe('Hidden Card');
        expect((card as any).hidden).toBe(true);
      }

      // Host sees Bob's reserveCard masked
      const bobReserve = filteredForHost.players[guest.playerId].reserveCard;
      expect(bobReserve).toBeDefined();
      expect(bobReserve?.id).toBe(-1);
      expect(bobReserve?.name).toBe('Hidden Reserve');
      expect((bobReserve as any).hidden).toBe(true);
    });

    it('reveals own hand to Player 2, and masks Player 1 cards', () => {
      const filteredForGuest = filterStateForPlayer(gameState, guest.playerId);

      // Guest sees Bob's cards fully
      expect(filteredForGuest.players[guest.playerId].hand[0].id).toBeGreaterThan(0);
      expect(filteredForGuest.players[guest.playerId].hand[0].name).not.toBe('Hidden Card');

      // Guest sees Alice's hand masked
      const aliceHand = filteredForGuest.players[host.playerId].hand;
      expect(aliceHand.length).toBe(5);
      for (const card of aliceHand) {
        expect(card.id).toBe(-1);
        expect(card.name).toBe('Hidden Card');
        expect((card as any).hidden).toBe(true);
      }
    });

    it('masks draw deck order so players cannot peek ahead', () => {
      const filtered = filterStateForPlayer(gameState, host.playerId);

      expect(filtered.deck.length).toBe(gameState.deck.length);
      for (const card of filtered.deck) {
        expect(card.id).toBe(-1);
        expect((card as any).hidden).toBe(true);
      }
    });

    it('preserves public tableau and score information for all players', () => {
      gameState.players[host.playerId].vpTokens = 12;
      gameState.players[guest.playerId].beeTokens = 3;

      const filtered = filterStateForPlayer(gameState, host.playerId);

      expect(filtered.players[host.playerId].vpTokens).toBe(12);
      expect(filtered.players[guest.playerId].beeTokens).toBe(3);
      expect(filtered.players[host.playerId].tableau.length).toBe(3);
      expect(filtered.players[guest.playerId].tableau.length).toBe(3);
    });
  });

  describe('Action Handling & Turn Progression', () => {
    it('validates card selection and prevents duplicate or unowned cards', () => {
      const host = roomManager.createRoom('Alice');
      roomManager.joinRoom(host.roomId, 'Bob');
      const room = roomManager.getRoom(host.roomId)!;
      const hostHand = room.gameState!.players[host.playerId].hand;

      // Duplicate card selection (tableau and reserve are identical)
      const resDup = roomManager.handleAction(host.roomId, host.playerId, {
        type: 'SUBMIT_SELECTION',
        tableauCardId: hostHand[0].id,
        reserveCardId: hostHand[0].id,
      });
      expect(resDup.success).toBe(false);
      expect(resDup.error).toContain('must be different');

      // Card not in hand
      const resNonExistent = roomManager.handleAction(host.roomId, host.playerId, {
        type: 'SUBMIT_SELECTION',
        tableauCardId: hostHand[0].id,
        reserveCardId: 99999,
      });
      expect(resNonExistent.success).toBe(false);
      expect(resNonExistent.error).toContain('present in player hand');
    });

    it('resolves round scoring and awards Bee tokens when both players submit selection & placement', () => {
      const host = roomManager.createRoom('Alice');
      const guest = roomManager.joinRoom(host.roomId, 'Bob');
      const room = roomManager.getRoom(host.roomId)!;

      const p1Hand = room.gameState!.players[host.playerId].hand;
      const p2Hand = room.gameState!.players[guest.playerId].hand;

      // Player 1 submits selection and placement (first card can go anywhere in 3x4)
      const res1 = roomManager.handleAction(host.roomId, host.playerId, {
        type: 'SUBMIT_SELECTION',
        tableauCardId: p1Hand[0].id,
        reserveCardId: p1Hand[1].id,
        position: { row: 1, col: 1 },
      });
      expect(res1.success).toBe(true);

      // Player 2 submits selection and placement
      const res2 = roomManager.handleAction(host.roomId, guest.playerId, {
        type: 'SUBMIT_SELECTION',
        tableauCardId: p2Hand[0].id,
        reserveCardId: p2Hand[1].id,
        position: { row: 0, col: 0 },
      });
      expect(res2.success).toBe(true);

      // Round 1 should now be resolved and transitioned to round 2!
      expect(room.gameState!.round).toBe(2);
      expect(room.gameState!.phase).toBe('DRAFT');

      // Both players should have completed scoring
      expect(room.gameState!.players[host.playerId].vpTokens).toBeGreaterThanOrEqual(0);
      expect(room.gameState!.players[guest.playerId].vpTokens).toBeGreaterThanOrEqual(0);

      // Lowest scorer (or both on tie) receives Bee token
      const bees =
        room.gameState!.players[host.playerId].beeTokens +
        room.gameState!.players[guest.playerId].beeTokens;
      expect(bees).toBeGreaterThanOrEqual(1);

      // Tableaus now contain the placed card
      expect(room.gameState!.players[host.playerId].tableau[1][1]).not.toBeNull();
      expect(room.gameState!.players[guest.playerId].tableau[0][0]).not.toBeNull();
    });

    it('enforces orthogonal adjacency for subsequent card placements', () => {
      const host = roomManager.createRoom('Alice');
      const guest = roomManager.joinRoom(host.roomId, 'Bob');
      const room = roomManager.getRoom(host.roomId)!;

      const p1Hand = room.gameState!.players[host.playerId].hand;
      const p2Hand = room.gameState!.players[guest.playerId].hand;

      // Complete round 1 placing at (1, 1)
      roomManager.handleAction(host.roomId, host.playerId, {
        type: 'SUBMIT_SELECTION',
        tableauCardId: p1Hand[0].id,
        reserveCardId: p1Hand[1].id,
        position: { row: 1, col: 1 },
      });
      roomManager.handleAction(host.roomId, guest.playerId, {
        type: 'SUBMIT_SELECTION',
        tableauCardId: p2Hand[0].id,
        reserveCardId: p2Hand[1].id,
        position: { row: 1, col: 1 },
      });

      // Now in Round 2: try to place at (0, 3) which is not adjacent to (1, 1)
      const p1HandR2 = room.gameState!.players[host.playerId].hand;
      const invalidAdjacency = roomManager.handleAction(host.roomId, host.playerId, {
        type: 'SUBMIT_SELECTION',
        tableauCardId: p1HandR2[0].id,
        reserveCardId: p1HandR2[1].id,
        position: { row: 0, col: 3 },
      });
      expect(invalidAdjacency.success).toBe(false);
      expect(invalidAdjacency.error).toContain('not valid');

      // Valid adjacent position: (1, 2) is adjacent to (1, 1)
      const p2HandR2 = room.gameState!.players[guest.playerId].hand;
      const validPlacement = roomManager.handleAction(host.roomId, guest.playerId, {
        type: 'SUBMIT_SELECTION',
        tableauCardId: p2HandR2[0].id,
        reserveCardId: p2HandR2[1].id,
        position: { row: 1, col: 2 },
      });
      expect(validPlacement.success).toBe(true);
    });
  });

  describe('Rematch Flow', () => {
    it('requires both players to confirm rematch before resetting game', () => {
      const host = roomManager.createRoom('Alice');
      const guest = roomManager.joinRoom(host.roomId, 'Bob');

      // Player 1 requests rematch
      const res1 = roomManager.handleRematch(host.roomId, host.playerId);
      expect(res1.success).toBe(true);
      expect(res1.restarted).toBe(false);

      // Player 2 confirms rematch
      const res2 = roomManager.handleRematch(host.roomId, guest.playerId);
      expect(res2.success).toBe(true);
      expect(res2.restarted).toBe(true);

      const room = roomManager.getRoom(host.roomId)!;
      expect(room.gameState!.round).toBe(1);
      expect(room.gameState!.phase).toBe('DRAFT');
      expect(room.gameState!.players[host.playerId].vpTokens).toBe(0);
      expect(room.gameState!.players[guest.playerId].vpTokens).toBe(0);
    });
  });

  describe('Disconnection and Reconnection', () => {
    it('reconnects a player with a valid session token', () => {
      const host = roomManager.createRoom('Alice');
      const guest = roomManager.joinRoom(host.roomId, 'Bob');

      // Disconnect Bob
      const room = roomManager.getRoom(host.roomId)!;
      room.players[guest.playerId].connected = false;

      // Reconnect with wrong token -> fails
      const badRecon = roomManager.reconnectPlayer(host.roomId, guest.playerId, 'bad-token');
      expect(badRecon.success).toBe(false);
      expect(badRecon.error).toContain('Invalid session token');

      // Reconnect with correct token -> succeeds
      const goodRecon = roomManager.reconnectPlayer(
        host.roomId,
        guest.playerId,
        guest.sessionToken
      );
      expect(goodRecon.success).toBe(true);
      expect(goodRecon.state).toBeDefined();
      expect(room.players[guest.playerId].connected).toBe(true);
    });

    it('handles socket disconnect and starts reconnect timeout', () => {
      const host = roomManager.createRoom('Alice');
      const room = roomManager.getRoom(host.roomId)!;

      const mockSocket: any = {
        readyState: 1,
        send: vi.fn(),
      };

      roomManager.bindSocket(mockSocket, host.roomId, host.playerId);
      expect(room.players[host.playerId].connected).toBe(true);

      roomManager.handleDisconnect(mockSocket, 500);
      expect(room.players[host.playerId].connected).toBe(false);
      expect(room.disconnectTimeouts.has(host.playerId)).toBe(true);
    });
  });
});
