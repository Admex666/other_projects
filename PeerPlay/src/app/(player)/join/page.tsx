export const dynamic = 'force-dynamic'

import JoinSessionForm from '@/components/JoinSessionForm'
import Link from 'next/link'

export default async function JoinPage({
  searchParams,
}: {
  searchParams: Promise<{ code?: string; error?: string }>
}) {
  const { code, error } = await searchParams

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-3 sm:p-5 font-sans">
      <div className="theme-card max-w-[400px] w-full p-5 sm:p-6 space-y-4">
        <div className="text-center">
          <h1 className="text-xl font-extrabold text-slate-900 tracking-tight">
            Csatlakozás a Játékhoz
          </h1>
        </div>

        <JoinSessionForm prefillCode={code} initialError={error} />

        <div className="text-center pt-2 border-t border-slate-100">
          <Link
            href="/"
            className="text-xs text-slate-400 hover:text-slate-700 transition font-medium"
          >
            ← Kezdőlap
          </Link>
        </div>
      </div>
    </div>
  )
}
