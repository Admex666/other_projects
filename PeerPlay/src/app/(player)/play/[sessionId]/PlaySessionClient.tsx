'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import ProductionPanel from '@/components/ProductionPanel'
import InventoryPanel from '@/components/InventoryPanel'
import TradeOfferForm from '@/components/TradeOfferForm'
import PendingTradesPanel from '@/components/PendingTradesPanel'
import BankPanel from '@/components/BankPanel'
import { getSessionDetails, } from '@/modules/session/actions'
import { getTradesForUser } from '@/modules/interaction/trade'
import useSWR from 'swr'

// Fetcher uses Server Action directly
const fetcher = async (sessionId: string) => {
    return await getSessionDetails(sessionId)
}

export default function PlaySessionClient({
    sessionId,
    initialUserId,
    initialSessionData
}: {
    sessionId: string,
    initialUserId: string,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    initialSessionData: any
}) {
    const router = useRouter()
    const [activeTab, setActiveTab] = useState<'trade' | 'inbox' | 'bank'>('trade')

    // SWR hook for real-time polling every 3 seconds inside active views 
    const { data: sessionData } = useSWR(sessionId, fetcher, {
        fallbackData: initialSessionData,
        refreshInterval: 3000,
        revalidateOnFocus: true
    })

    // We need the real session UUID (not joinCode) for TradeRequest queries
    // session is available immediately via fallbackData so session?.id is the UUID
    const sessionUUID = sessionData?.id ?? null

    const { data: trades } = useSWR(
        sessionUUID && initialUserId ? `trades-${sessionUUID}-${initialUserId}` : null,
        () => getTradesForUser(sessionUUID!, initialUserId!),
        { refreshInterval: 3000 }
    )

    const session = sessionData as any

    useEffect(() => {
        if (session && session.status === 'closed' && initialUserId) {
            router.push(`/survey/${session.id}?userId=${initialUserId}`)
        }
    }, [session, initialUserId, router])

    if (!session) return <div>Loading session...</div>

    const currentUserId = initialUserId

    if (!currentUserId) {
        return (
            <div className="p-8 text-center">
                <h1 className="text-xl font-bold text-red-600">Error: Missing User ID</h1>
                <p>Please join the session through the Join page to get a valid link.</p>
            </div>
        )
    }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const myParticipant = session.participants.find((p: any) => p.userId === currentUserId)
    const me = myParticipant?.user
    const myTeam = myParticipant?.team

    if (!me) {
        return (
            <div className="p-8 text-center text-red-600 font-bold">You are not a participant in this session.</div>
        )
    }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const otherParticipants = session.participants.filter((p: any) => p.userId !== currentUserId)

    return (
        <div className="min-h-screen bg-gray-50 p-6">
            <div className="max-w-4xl mx-auto space-y-6">

                <header className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex justify-between items-center">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">🌾 GLOBAL EXCHANGE: {session.scenario.name}</h1>
                        <p className="text-gray-500 text-sm">Belépve: <span className="font-semibold">{me.name}</span></p>
                    </div>
                    <div className="text-right">
                        <span className={`px-3 py-1 text-sm font-semibold rounded-full 
                  ${session.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                            Session {session.status.toUpperCase()}
                        </span>
                    </div>
                </header>

                {session.status === 'draft' ? (
                    <div className="bg-white p-12 text-center rounded-xl shadow-sm border border-gray-100 max-w-2xl mx-auto">
                        <h2 className="text-2xl font-black text-gray-800 tracking-tight">GLOBAL EXCHANGE</h2>
                        <div className="mt-8 mb-8 space-y-4">
                            <p className="text-gray-500 text-lg">Várj, amíg a HR elindítja a szimulációt.</p>
                            <p className="text-sm font-medium text-gray-600 border p-3 bg-gray-50 rounded inline-block">
                                Csatlakozottak: {session.participants.length}
                            </p>
                        </div>

                        <div className="p-6 bg-green-50 border border-green-100 rounded-lg text-left">
                            <h3 className="font-bold text-green-900 mb-2">🌾 A Farmod</h3>
                            <p className="text-green-800 text-lg">Farmot kapsz az indításkor</p>
                            <p className="text-sm text-green-600 mt-2">A farmok (Alpha, Beta, Gamma, Delta, Epsilon) elosztása az indításkor történik meg.</p>
                        </div>

                        <div className="mt-8 flex justify-center">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
                        </div>
                    </div>
                ) : (
                    <>
                        {!session.isRoundActive && (
                            <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded mb-6 shadow-sm">
                                <div className="flex">
                                    <div className="ml-3">
                                        <p className="text-sm text-yellow-700 font-bold">⏳ Várakozás a következő körre...</p>
                                        <p className="text-xs text-yellow-600 mt-1">A játék jelenleg szünetel. Kereskedni és termelni csak akkor lehet, ha a HR elindítja a kört.</p>
                                    </div>
                                </div>
                            </div>
                        )}
                        <div className={`grid grid-cols-1 md:grid-cols-3 gap-6 ${!session.isRoundActive ? 'opacity-60 pointer-events-none select-none filter grayscale-[30%] transition-all duration-500' : ''}`}>

                            {/* Left Column: Resources & Production */}
                            <div className="md:col-span-1 flex flex-col space-y-6">
                                {/* Resources / Me view */}
                                <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex flex-col items-center text-center">
                                    {myParticipant ? (
                                        <div className="w-full">
                                            <div className="w-full bg-slate-900 text-white rounded-t-lg p-3 font-black tracking-widest uppercase border-b-4 border-slate-700">
                                                {myTeam ? myTeam.name : 'Unknown Team'}
                                            </div>
                                            <div className="bg-slate-50 border-x border-b border-slate-200 rounded-b-lg p-4 space-y-3 shadow-inner">
                                                <div className="flex justify-between items-center p-2 bg-white rounded border shadow-sm">
                                                    <span className="font-medium text-green-800">💰 Tőke</span>
                                                    <span className="font-bold text-green-600">${myParticipant.capital.toLocaleString()}</span>
                                                </div>
                                                <div className="flex justify-between items-center p-2 bg-white rounded border shadow-sm">
                                                    <span className="font-medium text-amber-800">🌱 Vetőmag</span>
                                                    <span className="font-bold text-amber-600">{myParticipant.rawMaterial}</span>
                                                </div>
                                                <div className="flex justify-between items-center p-2 bg-white rounded border shadow-sm">
                                                    <span className="font-medium text-blue-800">⚙️ Gép (Tech)</span>
                                                    <span className="font-bold text-blue-600">{myParticipant.techLevel}</span>
                                                </div>
                                            </div>
                                        </div>
                                    ) : (
                                        <p className="text-red-500">Error: Missing participant data.</p>
                                    )}
                                </div>

                                {/* Production Panel */}
                                {myParticipant && <ProductionPanel sessionId={session.id} myParticipant={myParticipant} />}
                                {myParticipant && <InventoryPanel sessionId={session.id} userId={currentUserId} inventoryJson={myParticipant.inventory} />}
                            </div>

                            {/* Right Column: Tabbed Trade + Bank UI */}
                            <div className="md:col-span-2 space-y-0">
                                {/* Tab headers */}
                                <div className="flex border-b border-gray-200 mb-0">
                                    {(['trade', 'inbox', 'bank'] as const).map(tab => {
                                        const pendingCount = tab === 'inbox'
                                            ? (trades ?? []).filter((t: any) => t.toUserId === currentUserId && t.status === 'pending').length
                                            : 0
                                        const labels: Record<string, string> = { trade: '🤝 Trade', inbox: '📬 Ajánlatok', bank: '🏦 Bank' }
                                        return (
                                            <button
                                                key={tab}
                                                onClick={() => setActiveTab(tab)}
                                                className={`px-4 py-2.5 text-sm font-bold border-b-2 transition-colors ${activeTab === tab
                                                    ? 'border-indigo-600 text-indigo-600'
                                                    : 'border-transparent text-gray-500 hover:text-gray-700'
                                                    }`}
                                            >
                                                {labels[tab]}
                                                {pendingCount > 0 && (
                                                    <span className="ml-1.5 bg-red-500 text-white text-xs font-bold px-1.5 py-0.5 rounded-full">{pendingCount}</span>
                                                )}
                                            </button>
                                        )
                                    })}
                                </div>

                                {/* Tab content */}
                                <div className="mt-4 space-y-4">
                                    {activeTab === 'trade' && myParticipant && (
                                        <TradeOfferForm
                                            sessionId={session.id}
                                            currentUserId={currentUserId}
                                            // eslint-disable-next-line @typescript-eslint/no-explicit-any
                                            myParticipant={myParticipant as any}
                                            // eslint-disable-next-line @typescript-eslint/no-explicit-any
                                            otherParticipants={otherParticipants as any}
                                            onSent={() => setActiveTab('inbox')}
                                        />
                                    )}
                                    {activeTab === 'inbox' && (
                                        <PendingTradesPanel
                                            sessionId={session.id}
                                            currentUserId={currentUserId}
                                            // eslint-disable-next-line @typescript-eslint/no-explicit-any
                                            trades={(trades ?? []) as any}
                                        />
                                    )}
                                    {activeTab === 'bank' && myParticipant && (
                                        <BankPanel
                                            sessionId={session.id}
                                            userId={currentUserId}
                                            // eslint-disable-next-line @typescript-eslint/no-explicit-any
                                            participant={myParticipant as any}
                                        />
                                    )}
                                </div>
                            </div>

                        </div>
                    </>
                )}
            </div>
        </div>
    )
}
