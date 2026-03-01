'use client'

import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { createClient } from '@/utils/supabase/client'
import { useAuthStore } from '@/store/authStore'

export default function DashboardPage() {
    const router = useRouter()
    const supabase = createClient()
    const { user, setUser } = useAuthStore()
    const [roomName, setRoomName] = useState('')
    const [joinCode, setJoinCode] = useState('')
    const [loading, setLoading] = useState(false)

    const handleJoinRoom = () => {
        if (joinCode.length === 4) {
            router.push(`/join/${joinCode}`)
        }
    }

    useEffect(() => {
        supabase.auth.getUser().then(({ data }) => {
            if (!data.user) {
                router.push('/')
            } else {
                setUser(data.user)
            }
        })
    }, [supabase.auth, router, setUser])

    const handleCreateRoom = async (e: React.FormEvent) => {
        e.preventDefault()
        setLoading(true)
        try {
            const res = await fetch('/api/room/create', {
                method: 'POST',
                body: JSON.stringify({ name: roomName || `${user?.email}'s Ulti Room`, isPrivate: false }),
                headers: { 'Content-Type': 'application/json' }
            })
            const result = await res.json()
            if (result.room) {
                router.push(`/room/${result.room.short_code}`)
            } else {
                alert(result.error)
            }
        } finally {
            setLoading(false)
        }
    }

    const handleLogout = async () => {
        await supabase.auth.signOut()
        setUser(null)
        router.push('/')
    }

    if (!user) return null

    return (
        <div className="min-h-screen bg-slate-100 p-4 sm:p-8">
            <div className="max-w-4xl mx-auto space-y-8">

                {/* Header */}
                <div className="bg-white rounded-2xl p-6 shadow-sm flex justify-between items-center border border-slate-200">
                    <div>
                        <h1 className="text-2xl font-black text-slate-800">Üdvözlünk, <span className="text-red-600">{user.email?.split('@')[0]}!</span></h1>
                        <p className="text-slate-500">Itt indíthatsz új játékot vagy kereshetsz szobát.</p>
                    </div>
                    <button onClick={handleLogout} className="px-4 py-2 text-sm font-semibold text-slate-600 hover:text-red-600 bg-slate-50 hover:bg-red-50 rounded-lg transition-colors">
                        Kijelentkezés
                    </button>
                </div>

                <div className="grid md:grid-cols-2 gap-8">

                    {/* Create Room */}
                    <div className="bg-white rounded-2xl p-8 shadow-sm border border-slate-200">
                        <div className="w-12 h-12 bg-red-100 text-red-600 rounded-xl flex items-center justify-center text-2xl mb-6">🃏</div>
                        <h2 className="text-xl font-bold mb-2">Új Szoba Nyitása</h2>
                        <p className="text-slate-500 mb-6 text-sm">Hozz létre egy új szobát és hívd meg a barátaidat a linkkel.</p>

                        <form onSubmit={handleCreateRoom} className="space-y-4">
                            <input
                                type="text"
                                value={roomName}
                                onChange={(e) => setRoomName(e.target.value)}
                                placeholder="Pl. Péntek esti Ulti"
                                className="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-red-500 outline-none"
                            />
                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full bg-slate-900 hover:bg-black text-white font-bold py-3 rounded-xl transition-all shadow-md shadow-slate-900/20"
                            >
                                {loading ? 'Létrehozás...' : 'Szoba Indítása'}
                            </button>
                        </form>
                    </div>

                    {/* Quick Actions / Stats placeholder */}
                    <div className="bg-gradient-to-br from-red-600 to-rose-700 rounded-2xl p-8 shadow-lg text-white">
                        <h2 className="text-xl font-bold mb-2">Gyors Csatlakozás</h2>
                        <p className="opacity-80 mb-6 text-sm">Van 4 karakteres szobakódod? Írd be ide!</p>
                        <div className="flex space-x-2">
                            <input
                                type="text"
                                placeholder="Pl. ABC4"
                                className="flex-1 px-4 py-3 rounded-xl text-slate-900 outline-none uppercase font-bold tracking-widest"
                                maxLength={4}
                                value={joinCode}
                                onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
                                onKeyDown={(e) => e.key === 'Enter' && handleJoinRoom()}
                            />
                            <button onClick={handleJoinRoom} disabled={loading || joinCode.length !== 4} className="bg-white text-red-600 font-bold px-6 py-3 rounded-xl hover:bg-slate-50 transition-colors disabled:opacity-50">Hajrá!</button>
                        </div>
                    </div>
                </div>

            </div>
        </div>
    )
}
