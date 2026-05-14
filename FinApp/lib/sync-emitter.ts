import { EventEmitter } from 'events';

// Global singleton for event emitting across the app
declare global {
  var syncEmitter: EventEmitter | undefined;
}

export const syncEmitter = global.syncEmitter || new EventEmitter();

if (process.env.NODE_ENV !== 'production') {
  global.syncEmitter = syncEmitter;
}

// Event types
export const SYNC_EVENTS = {
  TRANSACTION_CREATED: 'transaction_created',
  POCKET_UPDATED: 'pocket_updated',
  DEBT_UPDATED: 'debt_updated',
};
