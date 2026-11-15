export const WORKSHOP_PHASES = [
  'PHASE_0_SETUP',
  'PHASE_1_PRE_SURVEY',
  'PHASE_2_RULES',
  'PHASE_3_PLANNING',
  'PHASE_4_ROUND_1',
  'PHASE_5_EVENT_1',
  'PHASE_6_ROUND_2',
  'PHASE_7_EVENT_2',
  'PHASE_8_ROUND_3',
  'PHASE_9_BANK_SETTLEMENT',
  'PHASE_10_POST_SURVEY',
  'PHASE_11_DEBRIEF',
] as const

export type WorkshopPhase = (typeof WORKSHOP_PHASES)[number] | 'POST_WORKPLACE_ONA'

export const PHASE_DEFAULT_DURATIONS: Record<WorkshopPhase, number> = {
  PHASE_0_SETUP: 300,
  PHASE_1_PRE_SURVEY: 300,
  PHASE_2_RULES: 480,
  PHASE_3_PLANNING: 300,
  PHASE_4_ROUND_1: 900,
  PHASE_5_EVENT_1: 180,
  PHASE_6_ROUND_2: 900,
  PHASE_7_EVENT_2: 180,
  PHASE_8_ROUND_3: 720,
  PHASE_9_BANK_SETTLEMENT: 420,
  PHASE_10_POST_SURVEY: 600,
  PHASE_11_DEBRIEF: 420,
  POST_WORKPLACE_ONA: 0,
}

export const PHASE_LABELS: Record<string, string> = {
  PHASE_0_SETUP: 'Előkészítés',
  PHASE_1_PRE_SURVEY: 'Kezdő felmérés',
  PHASE_2_RULES: 'Szabályismertetés',
  PHASE_3_PLANNING: 'Csapatstratégia',
  PHASE_4_ROUND_1: '1. Kereskedelmi kör',
  PHASE_5_EVENT_1: '1. Piaci esemény',
  PHASE_6_ROUND_2: '2. Kereskedelmi kör',
  PHASE_7_EVENT_2: '2. Piaci esemény',
  PHASE_8_ROUND_3: '3. Kereskedelmi kör',
  PHASE_9_BANK_SETTLEMENT: 'Banki elszámolás',
  PHASE_10_POST_SURVEY: 'Záró értékelés',
  PHASE_11_DEBRIEF: 'Eredményhirdetés',
  POST_WORKPLACE_ONA: 'Munkahelyi felmérés',
}

export function getPhaseLabel(phase: string): string {
  return PHASE_LABELS[phase] || 'Előkészítés'
}

export const SESSION_STATUS_LABELS: Record<string, string> = {
  DRAFT: 'Előkészítés alatt',
  ACTIVE: 'Folyamatban',
  COMPLETED: 'Lezárva',
  ARCHIVED: 'Archivált',
}

export function getStatusLabel(status: string): string {
  return SESSION_STATUS_LABELS[status] || status
}

export const TEAM_PROFILE_LABELS: Record<string, string> = {
  CAPITAL: 'Alfa',
  RESOURCE: 'Béta',
  TECH: 'Gamma',
  EMERGING: 'Delta',
}

export function getProfileLabel(code: string): string {
  return TEAM_PROFILE_LABELS[code] || code
}

export const TRADE_STATUS_LABELS: Record<string, string> = {
  PENDING: 'Függőben',
  ACCEPTED: 'Elfogadva',
  REJECTED: 'Elutasítva',
  DECLINED: 'Elutasítva',
  CANCELLED: 'Visszavonva',
  EXPIRED_REFUNDED: 'Lejárt (visszatérítve)',
}

export function getTradeStatusLabel(status: string): string {
  return TRADE_STATUS_LABELS[status] || status
}

export const SHAPE_LABELS: Record<string, string> = {
  SQUARE: 'Négyzet',
  TRIANGLE: 'Háromszög',
  CIRCLE: 'Kör',
  RECTANGLE: 'Téglalap',
  PREMIUM_PACK: 'Prémium Csomag',
}

export function getShapeLabel(shape: string): string {
  return SHAPE_LABELS[shape] || shape
}
