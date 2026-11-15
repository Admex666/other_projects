import { NextResponse } from 'next/server'
import { getSessionDetails } from '@/modules/session/actions'

export const dynamic = 'force-dynamic'

export async function GET(
  _req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    if (!id) {
      return NextResponse.json({ error: 'Missing session ID' }, { status: 400 })
    }
    const session = await getSessionDetails(id)
    if (!session) {
      return NextResponse.json({ error: 'Session not found' }, { status: 404 })
    }

    const nowMs = Date.now()
    const startedMs = session.phaseStartedAt
      ? new Date(session.phaseStartedAt).getTime()
      : nowMs
    const elapsedSec = Math.max(0, Math.floor((nowMs - startedMs) / 1000))
    const computedRemainingSeconds = session.isTimerPaused
      ? Math.max(0, session.timerRemainingSeconds || 0)
      : Math.max(0, (session.phaseDurationSeconds || 0) - elapsedSec)

    return NextResponse.json(
      {
        ...session,
        serverNowMs: nowMs,
        computedRemainingSeconds,
      },
      {
        headers: {
          'Cache-Control': 'no-store, no-cache, must-revalidate, proxy-revalidate',
          Pragma: 'no-cache',
          Expires: '0',
        },
      }
    )
  } catch (err: any) {
    console.error('GET /api/session/[id] error:', err)
    return NextResponse.json(
      { error: err.message || 'Failed to load session' },
      { status: 500 }
    )
  }
}
