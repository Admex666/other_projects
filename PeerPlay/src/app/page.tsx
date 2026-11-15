import Link from 'next/link'
import TunnelAccessCard from '@/components/home/TunnelAccessCard'

export default function Home() {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-3 sm:p-5 font-sans">
      <div className="theme-card max-w-lg w-full p-5 sm:p-6 space-y-4 text-center">
        {/* Compact Header */}
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          The Trading Game
        </h1>

        {/* Compact QR & Tunnel Access Card */}
        <TunnelAccessCard />

        {/* Simple, Direct Portal Buttons */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-1">
          <Link
            href="/dashboard"
            className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-bold shadow-xs transition flex items-center justify-center gap-2"
          >
            <span>Facilitátori Irányítópult</span>
            <span>→</span>
          </Link>

          <Link
            href="/join"
            className="w-full py-3 px-4 bg-white hover:bg-slate-50 border border-slate-200 text-slate-800 rounded-xl text-sm font-bold shadow-2xs transition flex items-center justify-center gap-2"
          >
            <span>Résztvevői Belépés</span>
            <span>→</span>
          </Link>
        </div>
      </div>
    </div>
  )
}
