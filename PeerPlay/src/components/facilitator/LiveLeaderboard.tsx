'use client'

interface Participant {
  id: string
  user: {
    id: string
    name: string
    email: string
    role?: string | null
  }
}

interface TeamData {
  id: string
  name: string
  profileCode: string
  cashBalance: number
  paperSheets: number
  scissorsCount: number
  rulersCount: number
  templatesCount: number
  participants?: Participant[]
}

interface LiveLeaderboardProps {
  teams: TeamData[]
}

export default function LiveLeaderboard({ teams }: LiveLeaderboardProps) {
  // Estimated asset valuation: Paper: $20, Scissors: $100, Rulers: $50, Templates: $150
  const rankedTeams = [...teams].map((team) => {
    const assetValuation =
      team.paperSheets * 20 +
      team.scissorsCount * 100 +
      team.rulersCount * 50 +
      team.templatesCount * 150
    const totalWealth = team.cashBalance + assetValuation
    return {
      ...team,
      totalWealth,
      assetValuation,
    }
  }).sort((a, b) => b.totalWealth - a.totalWealth)

  return (
    <div className="theme-card p-6 space-y-4">
      <div className="flex justify-between items-center pb-3 border-b border-slate-100">
        <div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
            Élő Vállalati Rangsor & Készletállomány
          </h3>
          <p className="text-xs text-slate-500">
            Valós idejű vagyonértékelés (Készpénz + Nyilvántartott eszközérték)
          </p>
        </div>
        <span className="text-xs font-mono text-slate-400">
          {teams.length} Vállalat Versenyben
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-100 text-left">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-4 py-2.5 text-[11px] font-mono font-semibold text-slate-500 uppercase tracking-wider">
                Helyezés & Vállalat
              </th>
              <th className="px-4 py-2.5 text-[11px] font-mono font-semibold text-slate-500 uppercase tracking-wider text-right">
                Készpénz
              </th>
              <th className="px-4 py-2.5 text-[11px] font-mono font-semibold text-slate-500 uppercase tracking-wider text-center">
                A4 Lapok
              </th>
              <th className="px-4 py-2.5 text-[11px] font-mono font-semibold text-slate-500 uppercase tracking-wider text-center">
                Olló
              </th>
              <th className="px-4 py-2.5 text-[11px] font-mono font-semibold text-slate-500 uppercase tracking-wider text-center">
                Sablon
              </th>
              <th className="px-4 py-2.5 text-[11px] font-mono font-semibold text-slate-500 uppercase tracking-wider text-right">
                Teljes Vagyon
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 bg-white">
            {rankedTeams.map((team, idx) => {
              const isFirst = idx === 0
              return (
                <tr key={team.id} className={isFirst ? 'bg-blue-50/30' : 'hover:bg-slate-50/50'}>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <div className="flex items-center gap-2.5">
                      <span
                        className={`w-6 h-6 rounded-full flex items-center justify-center font-mono font-bold text-xs ${
                          isFirst
                            ? 'bg-blue-600 text-white shadow-2xs'
                            : 'bg-slate-100 text-slate-700'
                        }`}
                      >
                        {idx + 1}
                      </span>
                      <div>
                        <div className="text-xs font-bold text-slate-900">{team.name}</div>
                        <span className="text-[10px] font-mono text-slate-400 uppercase">
                          {team.profileCode} · {team.participants?.length || 0} fő
                        </span>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-right font-mono font-bold text-xs text-slate-900 tabular-nums">
                    ${team.cashBalance}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-center font-mono text-xs text-slate-700 tabular-nums">
                    {team.paperSheets} lap
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-center font-mono text-xs text-slate-700 tabular-nums">
                    {team.scissorsCount} db
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-center font-mono text-xs text-slate-700 tabular-nums">
                    {team.templatesCount} db
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-right font-mono font-extrabold text-sm text-blue-600 tabular-nums">
                    ${team.totalWealth}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Participants breakdown */}
      <div className="pt-3 border-t border-slate-100 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
        {teams.map((t) => (
          <div key={t.id} className="p-3 bg-slate-50/60 rounded-lg border border-slate-100">
            <span className="text-[10px] font-mono font-bold text-slate-400 uppercase block">
              {t.name} Csapattagok ({t.participants?.length || 0})
            </span>
            <div className="mt-1 space-y-1">
              {t.participants && t.participants.length > 0 ? (
                t.participants.map((p) => (
                  <div key={p.id} className="text-[11px] text-slate-700 truncate font-medium">
                    {p.user.name}
                  </div>
                ))
              ) : (
                <div className="text-[11px] text-slate-400 italic">Még nincs csatlakozott tag</div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
