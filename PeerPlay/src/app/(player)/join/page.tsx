export const dynamic = 'force-dynamic'

import JoinSessionForm from '@/components/JoinSessionForm'
import Link from 'next/link'

export default async function JoinPage({
  searchParams,
}: {
  searchParams: Promise<{ code?: string }>
}) {
  const { code } = await searchParams

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4 sm:p-6 font-sans">
      <div className="theme-card max-w-[420px] w-full p-6 sm:p-8 space-y-6">
        {/* Brand Header */}
        <div className="text-center space-y-1">
          <div className="flex items-center justify-center gap-1.5 mb-2">
            <span className="w-2 h-2 rounded-full bg-blue-600"></span>
            <span className="text-[10px] font-mono font-bold uppercase tracking-widest text-slate-500">
              PeerPlay Enterprise
            </span>
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            The Trading Game
          </h1>
          <p className="text-xs text-slate-500">
            Jelszómentes gyors becsatlakozás okostelefonról
          </p>
        </div>

        {/* Join Form Component */}
        <JoinSessionForm prefillCode={code} />

        {/* Footer */}
        <div className="text-center pt-2 border-t border-slate-100">
          <Link
            href="/dashboard"
            className="text-xs text-slate-400 hover:text-slate-700 transition font-medium"
          >
            ← Vissza a facilitátori felületre
          </Link>
        </div>
      </div>
    </div>
  )
}
