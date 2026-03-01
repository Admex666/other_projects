'use client'

import React, { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { createClient } from '@/utils/supabase/client'
import { useAuthStore } from '@/store/authStore'
import { useRoomStore, Room } from '@/store/roomStore'

export default function RoomPage({ params }: { params: Promise<{ id: string }> }) {
    const { id: roomId } = React.use(params)
    const router = useRouter()
    const supabase = createClient()
    const { user } = useAuthStore()
    const { currentRoom, setCurrentRoom } = useRoomStore()

    const [isNotFound, setIsNotFound] = React.useState(false)

    useEffect(() => {
        if (!user) {
            router.push('/')
            return
        }

        let channel: any;
        let isMounted = true;

        const fetchRoom = async () => {
            const { data, error } = await supabase.from('rooms').select('*, host:profiles!host_id(username)').eq('short_code', roomId.toUpperCase()).single()
            if (error || !data) {
                if (isMounted) setIsNotFound(true)
                return
            }
            if (!isMounted) return;

            setCurrentRoom(data as any)

            // Listen for room updates using the actual database UUID from data.id
            channel = supabase.channel(`room_${data.id}`)
                .on('postgres_changes', { event: 'UPDATE', schema: 'public', table: 'rooms', filter: `id=eq.${data.id}` },
                    (payload) => {
                        console.log('Realtime UPDATE received:', payload)
                        const updatedRoom = payload.new as any

                        // Merge with existing state to preserve joined relations like 'host:profiles'
                        const currentObj = useRoomStore.getState().currentRoom;
                        const mergedRoom = { ...currentObj, ...updatedRoom };

                        setCurrentRoom(mergedRoom)

                        if (mergedRoom.status === 'playing') {
                            // Transition everyone to game board using the short code
                            router.push(`/game/${mergedRoom.short_code}`)
                        }
                    })
                .subscribe((status) => {
                    console.log(`Supabase Realtime channel status: ${status}`)
                })
        }
        fetchRoom()

        return () => {
            isMounted = false;
            if (channel) supabase.removeChannel(channel)
        }
    }, [roomId, user, router, setCurrentRoom])

    if (isNotFound) return (
        <div className="min-h-screen bg-slate-100 flex items-center justify-center p-4">
            <div className="bg-white max-w-md w-full rounded-2xl shadow-xl p-8 text-center border border-slate-200">
                <div className="text-6xl mb-4">🕵️‍♂️</div>
                <h1 className="text-2xl font-black text-slate-800 mb-2">A Szoba Nem Található</h1>
                <p className="text-slate-500 mb-8">Ellenőrizd a szobakódot! Lehetséges, hogy a játék már véget ért vagy rossz linket kaptál.</p>
                <button onClick={() => router.push('/dashboard')} className="bg-red-600 text-white font-bold px-6 py-3 rounded-xl hover:bg-red-700 w-full transition-colors">Vissza a Kezdőlapra</button>
            </div>
        </div>
    )

    if (!currentRoom || !user) return <div className="p-8 text-center bg-slate-100 min-h-[100vh] font-bold text-slate-500">Szoba betöltése...</div>

    const isHost = currentRoom.host_id === user.id
    const playerCount = [currentRoom.player1_id, currentRoom.player2_id, currentRoom.player3_id].filter(Boolean).length

    const handleStartGame = async () => {
        try {
            const res = await fetch('/api/game/start', {
                method: 'POST',
                body: JSON.stringify({ roomId: currentRoom.id }),
                headers: { 'Content-Type': 'application/json' }
            })
            const result = await res.json()
            if (result.error) alert(result.error)
            else router.push(`/game/${currentRoom.short_code}`)
        } catch (err) {
            console.error(err)
        }
    }

    // Generate Invite Link
    const inviteLink = `${window.location.origin}/join/${currentRoom.id}`

    return (
        <div className="min-h-screen bg-slate-100 flex items-center justify-center p-4">
            <div className="bg-white max-w-lg w-full rounded-2xl shadow-2xl p-8 text-center">

                <h1 className="text-3xl font-black text-slate-800 mb-2">{currentRoom.name}</h1>
                <p className="text-slate-500 font-medium mb-8">
                    {currentRoom.is_private ? '🔒 Privát Szoba' : '🌍 Nyilvános Szoba'}
                </p>

                <div className="flex justify-center items-center space-x-4 mb-8">
                    <div className={`w-16 h-16 rounded-full border-4 flex items-center justify-center font-bold text-xl ${currentRoom.player1_id ? 'border-green-500 bg-green-100 text-green-700' : 'border-slate-200 bg-slate-50'}`}>P1</div>
                    <div className={`w-16 h-16 rounded-full border-4 flex items-center justify-center font-bold text-xl ${currentRoom.player2_id ? 'border-green-500 bg-green-100 text-green-700' : 'border-slate-200 bg-slate-50 text-slate-300'}`}>P2</div>
                    <div className={`w-16 h-16 rounded-full border-4 flex items-center justify-center font-bold text-xl ${currentRoom.player3_id ? 'border-green-500 bg-green-100 text-green-700' : 'border-slate-200 bg-slate-50 text-slate-300'}`}>P3</div>
                </div>

                <h3 className="font-bold text-lg mb-2">Várakozás a játékosokra... ({playerCount}/3)</h3>

                <div className="bg-slate-50 p-6 rounded-xl border border-slate-200 mb-8">
                    <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">A Szoba Kódja (PIN)</p>
                    <div className="text-5xl font-black text-red-600 tracking-[0.5em] ml-[0.5em]">
                        {currentRoom.short_code}
                    </div>
                    <p className="text-xs text-slate-400 mt-4">Oszd meg a fenti kódot a barátaiddal a csatlakozáshoz!</p>
                </div>

                {isHost ? (
                    <button
                        onClick={handleStartGame}
                        disabled={playerCount < 3}
                        className={`w-full py-4 rounded-xl font-black text-white text-lg transition-all ${playerCount === 3 ? 'bg-red-600 hover:bg-red-700 shadow-lg hover:shadow-red-500/30' : 'bg-slate-300 cursor-not-allowed hidden'}`}
                    >
                        JÁTÉK INDÍTÁSA
                    </button>
                ) : (
                    <div className="bg-amber-50 text-amber-700 p-4 rounded-xl font-medium border border-amber-200">
                        A szobagazda indíthatja a játékot, amint megvan a 3 fő!
                    </div>
                )}

            </div>
        </div>
    )
}
