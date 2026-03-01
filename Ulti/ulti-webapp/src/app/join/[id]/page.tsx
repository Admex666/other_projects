'use client'

import React, { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/store/authStore'

export default function JoinPage({ params }: { params: Promise<{ id: string }> }) {
    const { id: roomId } = React.use(params)
    const router = useRouter()
    const { user } = useAuthStore()
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        if (!user) {
            // Ha nincs bejelentkezve, vigyük vissza a főoldalra
            // de mentsük el, hova akart menni? Most szimpla redirect.
            router.push('/')
            return
        }

        const joinRoom = async () => {
            try {
                const res = await fetch('/api/room/join', {
                    method: 'POST',
                    body: JSON.stringify({ roomId: roomId }),
                    headers: { 'Content-Type': 'application/json' }
                })
                const data = await res.json()

                if (data.error) {
                    alert(data.error)
                    router.push('/dashboard')
                } else {
                    router.push(`/room/${roomId}`)
                }
            } catch (err) {
                console.error(err)
                alert("Hiba történt a csatlakozás során.")
            }
        }

        joinRoom()
    }, [roomId, user, router])

    return (
        <div className="min-h-screen flex items-center justify-center bg-slate-900 text-white flex-col space-y-4">
            <div className="w-16 h-16 border-4 border-red-500 border-t-transparent rounded-full animate-spin"></div>
            <h2 className="text-xl font-bold">Csatlakozás a szobához...</h2>
        </div>
    )
}
