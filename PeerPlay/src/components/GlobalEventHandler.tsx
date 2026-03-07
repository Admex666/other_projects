'use client'

import { useEffect, useState, useRef } from 'react'
import { toast } from 'react-hot-toast'

interface Props {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    session: any
}

export default function GlobalEventHandler({ session }: Props) {
    const lastEventId = useRef<string | null>(null)
    const [activeEvent, setActiveEvent] = useState<any>(null)
    const [timeLeft, setTimeLeft] = useState<number | null>(null)

    useEffect(() => {
        if (!session?.globalState) return

        try {
            const state = JSON.parse(session.globalState)
            const latestEvent = state.latestEvent

            // Handle timer logic
            if (latestEvent && latestEvent.type !== 'clear') {
                const expiresAt = state.eventExpiresAt
                if (expiresAt) {
                    const diff = new Date(expiresAt).getTime() - Date.now()
                    if (diff > 0) {
                        setActiveEvent(latestEvent)
                        // Csak akkor csapjuk fel az értéket, ha jelentősen eltér a kliens oldalon már számolttól (ne ugráljon az SWR miatt másodpercenként)
                        // Vagy hagyatkozhatunk az on-mount szinkronra. Ahhoz hogy sima legyen:
                        setTimeLeft((prev) => {
                            if (prev === null || Math.abs(prev - Math.floor(diff / 1000)) > 3) {
                                return Math.floor(diff / 1000)
                            }
                            return prev;
                        })
                    } else {
                        setActiveEvent(null)
                    }
                } else {
                    setActiveEvent(latestEvent)
                    setTimeLeft(null)
                }
            } else {
                setActiveEvent(null)
            }

            // Notification logic
            if (latestEvent && latestEvent.id !== lastEventId.current) {
                // Nem mutatjuk az első mountoláskor azonnal, ha már nagyon régi az event 
                // Ehelyett csak akkor mutatjuk, ha új (state change) történik időközben.
                // Viszont ha csak simán SWR refresh jön, és az SWR is hozza ugyanazt az old event-et, a lastEventId védeni fog.
                // Mivel az első renderkor 'null' a lastEventId, beállítjuk rögtön toast nélkül, hogy visszamenőleg ne szemeteljük tele a UI-t belépéskor.

                if (lastEventId.current === null) {
                    lastEventId.current = latestEvent.id
                    return
                }

                toast(latestEvent.message, {
                    icon: latestEvent.icon || 'ℹ️',
                    duration: 6000,
                    style: {
                        borderRadius: '10px',
                        background: '#333',
                        color: '#fff',
                        fontWeight: 'bold'
                    },
                })
                lastEventId.current = latestEvent.id
            }
        } catch (e) {
            console.error("Failed to parse global state for events", e)
        }
    }, [session?.globalState])

    useEffect(() => {
        if (timeLeft === null || timeLeft <= 0) return
        const interval = setInterval(() => {
            setTimeLeft(prev => {
                if (prev !== null && prev > 0) return prev - 1
                return 0
            })
        }, 1000)
        return () => clearInterval(interval)
    }, [timeLeft])

    if (!activeEvent || (timeLeft !== null && timeLeft <= 0)) return null

    return (
        <div className="fixed bottom-6 right-6 z-[9999] bg-indigo-900 border-2 border-indigo-400 shadow-[0_0_20px_rgba(99,102,241,0.5)] text-white p-4 rounded-xl max-w-sm">
            <h4 className="font-black text-lg flex items-center gap-2 mb-1">
                <span className="text-2xl">{activeEvent.icon}</span> AKTÍV ESEMÉNY!
            </h4>
            <p className="text-sm text-indigo-100 mb-2 leading-tight">{activeEvent.message}</p>
            {timeLeft !== null && (
                <div className="text-3xl font-mono font-black text-yellow-300 text-right tabular-nums tracking-widest mt-3">
                    {Math.floor(timeLeft / 60)}:{(timeLeft % 60).toString().padStart(2, '0')}
                </div>
            )}
        </div>
    )
}
