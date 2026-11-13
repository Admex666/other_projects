export const dynamic = 'force-dynamic'

import { getSessions } from '@/modules/session/actions'
import CreateSessionForm from '@/components/CreateSessionForm'
import prisma from '@/lib/prisma'
import Link from 'next/link'

export default async function DashboardPage() {
  let org = await prisma.organization.findFirst()
  if (!org) {
    org = await prisma.organization.create({
      data: {
        name: 'Demo Enterprise Zrt.',
        industry: 'Fintech & Tech',
      },
    })
  }

  const sessions = await getSessions()

  return (
    <div className="min-h-screen bg-slate-50 p-6 md:p-10 font-sans">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Top Header */}
        <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-200">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-mono font-bold tracking-wider uppercase text-blue-600 bg-blue-50 px-2.5 py-0.5 rounded border border-blue-100">
                PeerPlay Facilitator Console
              </span>
              <span className="text-xs text-slate-500 font-mono">v2.0 MVP</span>
            </div>
            <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-slate-900">
              Vállalati Munkamenetek & Szimulációk
            </h1>
            <p className="text-slate-500 text-sm mt-1">
              Szervezet: <span className="font-semibold text-slate-700">{org.name}</span> · The Trading Game vezérlőközpont
            </p>
          </div>
          <CreateSessionForm orgId={org.id} />
        </header>

        {/* Sessions Table Card */}
        <div className="theme-card overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/50 flex justify-between items-center">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-600">
              Rögzített Munkamenetek ({sessions.length})
            </h2>
            <Link
              href="/join"
              target="_blank"
              className="text-xs text-blue-600 hover:text-blue-700 font-semibold flex items-center gap-1"
            >
              <span>Résztvevői Belépési Oldal</span>
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
              </svg>
            </Link>
          </div>

          <table className="min-w-full divide-y divide-slate-100 text-left">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-6 py-3 text-xs font-mono font-semibold text-slate-500 uppercase tracking-wider">
                  Munkamenet & Kód
                </th>
                <th className="px-6 py-3 text-xs font-mono font-semibold text-slate-500 uppercase tracking-wider">
                  Fázis
                </th>
                <th className="px-6 py-3 text-xs font-mono font-semibold text-slate-500 uppercase tracking-wider">
                  Státusz
                </th>
                <th className="px-6 py-3 text-xs font-mono font-semibold text-slate-500 uppercase tracking-wider">
                  Csapatok
                </th>
                <th className="px-6 py-3 text-xs font-mono font-semibold text-slate-500 uppercase tracking-wider">
                  Tranzakciók
                </th>
                <th className="px-6 py-3 text-right text-xs font-mono font-semibold text-slate-500 uppercase tracking-wider">
                  Vezérlés
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {sessions.map((session) => (
                <tr key={session.id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="font-semibold text-slate-900 text-sm">
                      {session.name || 'The Trading Game'}
                    </div>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="font-mono text-xs font-bold bg-slate-100 text-slate-800 px-2 py-0.5 rounded border border-slate-200 tracking-wider">
                        PIN: {session.joinCode}
                      </span>
                      <span className="text-xs text-slate-400 font-mono">
                        {new Date(session.createdAt).toLocaleDateString('hu-HU')}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="font-mono text-xs text-slate-700 bg-slate-100 px-2 py-1 rounded">
                      {session.currentPhase}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                        session.status === 'ACTIVE'
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : session.status === 'COMPLETED'
                          ? 'bg-slate-100 text-slate-700 border border-slate-200'
                          : 'bg-amber-50 text-amber-700 border border-amber-200'
                      }`}
                    >
                      {session.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600 font-mono">
                    {session.teams.length} Vállalat
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600 font-mono">
                    {session._count.tradeTransactions} csere · {session._count.bankSales} banki
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                    <div className="flex items-center justify-end gap-2">
                      <Link
                        href={`/sessions/${session.id}`}
                        className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-2xs transition-colors"
                      >
                        Facilitátori Konzol
                      </Link>
                      <Link
                        href={`/sessions/${session.id}/debrief`}
                        className="px-3 py-1.5 border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-semibold transition-colors"
                      >
                        Debrief Kivetítő
                      </Link>
                    </div>
                  </td>
                </tr>
              ))}
              {sessions.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-slate-500 text-sm">
                    Még nincs létrehozott szimulációs munkamenet. Kattints a fenti &ldquo;Új Munkamenet&rdquo; gombra a kezdéshez!
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
