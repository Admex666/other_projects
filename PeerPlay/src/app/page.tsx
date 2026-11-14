import Link from 'next/link'
import TunnelAccessCard from '@/components/home/TunnelAccessCard'

export default function Home() {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4 sm:p-6 font-sans">
      <div className="theme-card max-w-xl w-full p-6 sm:p-8 space-y-6 text-center">
        {/* Brand Header */}
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full bg-blue-50 border border-blue-200 text-blue-700 text-xs font-mono font-bold uppercase tracking-wider">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-600"></span>
            PeerPlay Enterprise
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
            The Trading Game
          </h1>
          <p className="text-sm text-slate-500 max-w-md mx-auto leading-relaxed">
            Viselkedésszimuláció-alapú szervezetdiagnosztikai és hálózatelemzési platform.
          </p>
        </div>

        {/* Live Tunnel & QR Code Access Card */}
        <TunnelAccessCard />

        {/* Portal Links */}
        <div className="space-y-3 pt-1">
          <Link
            href="/dashboard"
            className="group block w-full p-4 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-bold shadow-xs transition-all text-left flex items-center justify-between"
          >
            <div>
              <div className="text-base font-extrabold flex items-center gap-2">
                <span>Facilitátori Irányítópult</span>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-blue-500/80 text-blue-100 font-semibold border border-blue-400">
                  PIN Védett
                </span>
              </div>
              <div className="text-xs text-blue-100 font-normal mt-0.5">
                Munkamenetek vezérlése, Banki pult, Piaci sokkok és Debrief
              </div>
            </div>
            <svg className="w-5 h-5 text-blue-200 group-hover:text-white group-hover:translate-x-0.5 transition-all shrink-0 ml-2" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
            </svg>
          </Link>

          <Link
            href="/join"
            className="group block w-full p-4 bg-white hover:bg-slate-50 border border-slate-200 text-slate-800 rounded-xl font-bold shadow-2xs transition-all text-left flex items-center justify-between"
          >
            <div>
              <div className="text-base font-extrabold">Résztvevői Belépés (PC teszt)</div>
              <div className="text-xs text-slate-500 font-normal mt-0.5">
                Csatlakozás helyi böngészőből PIN kóddal
              </div>
            </div>
            <svg className="w-5 h-5 text-slate-400 group-hover:text-slate-800 group-hover:translate-x-0.5 transition-all shrink-0 ml-2" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
            </svg>
          </Link>
        </div>

        {/* Footer info */}
        <div className="pt-4 border-t border-slate-100 text-[11px] font-mono text-slate-400 flex items-center justify-between">
          <span>PeerPlay Enterprise Platform</span>
          <span>v2.0 MVP Release</span>
        </div>
      </div>
    </div>
  )
}
