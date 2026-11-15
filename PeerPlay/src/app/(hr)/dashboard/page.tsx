export const dynamic = 'force-dynamic'

import { getSessions } from '@/modules/session/actions'
import { getPhaseLabel, getStatusLabel } from '@/modules/session/constants'
import CreateSessionForm from '@/components/CreateSessionForm'
import prisma from '@/lib/prisma'
import Link from 'next/link'

export default async function DashboardPage() {
  let org = await prisma.organization.findFirst()
  if (!org) {
    org = await prisma.organization.create({
      data: {
        name: 'Demó Vállalat Zrt.',
        industry: 'Technológia',
      },
    })
  }

  const sessions = await getSessions()

  return (
    <div className="min-h-screen bg-slate-50 p-4 sm:p-6 font-sans">
      <div className="max-w-5xl mx-auto space-y-5">
        {/* Compact Top Header */}
        <header className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-200">
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="text-slate-400 hover:text-slate-700 transition p-1.5 rounded-lg hover:bg-slate-200/60"
              title="Kezdőlap"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
              </svg>
            </Link>
            <div>
              <h1 className="text-xl sm:text-2xl font-extrabold tracking-tight text-slate-900">
                Facilitátori Irányítópult
              </h1>
            </div>
          </div>
          <CreateSessionForm orgId={org.id} />
        </header>

        {/* Responsive Session List (Visible in ANY window width / aspect ratio) */}
        <div className="theme-card overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-100 bg-slate-50/60 flex flex-wrap justify-between items-center gap-2">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-600">
              Munkamenetek ({sessions.length})
            </h2>
            <Link
              href="/join"
              target="_blank"
              className="text-xs text-blue-600 hover:text-blue-700 font-bold flex items-center gap-1"
            >
              <span>Résztvevői Belépés →</span>
            </Link>
          </div>

          <div className="divide-y divide-slate-100 bg-white">
            {sessions.map((session) => (
              <div
                key={session.id}
                className="p-4 hover:bg-slate-50/70 transition-colors flex flex-wrap items-center justify-between gap-3"
              >
                {/* Left: Name + PIN + Status */}
                <div className="min-w-[180px] flex-1 space-y-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <Link
                      href={`/sessions/${session.id}`}
                      className="font-bold text-slate-900 hover:text-blue-600 text-sm sm:text-base transition"
                    >
                      {session.name || 'Kereskedelmi Szimuláció'}
                    </Link>
                    <span className="font-mono text-xs font-black bg-blue-50 text-blue-700 px-2 py-0.5 rounded border border-blue-200">
                      PIN: {session.joinCode}
                    </span>
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold ${
                        session.status === 'ACTIVE'
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : session.status === 'COMPLETED'
                          ? 'bg-slate-100 text-slate-700 border border-slate-200'
                          : 'bg-amber-50 text-amber-700 border border-amber-200'
                      }`}
                    >
                      {getStatusLabel(session.status)}
                    </span>
                  </div>
                  <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500 font-medium">
                    <span className="text-slate-700 font-semibold">{getPhaseLabel(session.currentPhase)}</span>
                    <span>·</span>
                    <span>{session.teams.length} csapat</span>
                  </div>
                </div>

                {/* Right: Always-visible Action Buttons */}
                <div className="flex flex-wrap items-center gap-2 shrink-0">
                  <Link
                    href={`/sessions/${session.id}`}
                    className="px-3.5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold shadow-2xs transition"
                  >
                    Belépés (Konzol) →
                  </Link>
                  <Link
                    href={`/play/${session.id}`}
                    className="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-lg text-xs font-semibold transition"
                  >
                    Csapatpult
                  </Link>
                  <Link
                    href={`/sessions/${session.id}/debrief`}
                    className="px-3 py-2 border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-semibold transition"
                  >
                    Eredmények
                  </Link>
                </div>
              </div>
            ))}

            {sessions.length === 0 && (
              <div className="px-6 py-10 text-center text-slate-500 text-sm">
                Még nincs munkamenet. Kattints az „Új Munkamenet” gombra!
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
