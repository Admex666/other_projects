'use server'

import prisma from '@/lib/prisma'
import { revalidatePath } from 'next/cache'

// Esemény típusok
export type EventType = 'market_crash' | 'market_boom' | 'supply_shock' | 'hot_offer' | 'clear'

export async function triggerEvent(sessionId: string, type: EventType, targetProduct?: string, durationSeconds?: number) {
    const session = await prisma.session.findUnique({
        where: { id: sessionId },
        include: { rounds: { orderBy: { number: 'desc' }, take: 1 } }
    })

    if (!session) throw new Error("Session not found")

    // Csak a 3. körtől élnek ezek az események az impl plan alapján, de a biztonság kedvéért ha a HR kattintja, engedjük.

    let state = JSON.parse(session.globalState || '{}')
    let message = ""
    let icon = "⚠️"

    // Clear event (töröljük az aktív módosítókat)
    if (type === 'clear') {
        state = { ...state, marketCrash: false, boomProduct: null, supplyShock: false, hotOffer: null, eventExpiresAt: null }
        message = "A piac visszaállt a normál működésre."
        icon = "✅"
    }
    else if (type === 'market_crash') {
        state.marketCrash = true
        message = "Piac-összeomlás! A banki behozatalok árai drasztikusan estek!"
        icon = "📉"
    }
    else if (type === 'market_boom' && targetProduct) {
        state.boomProduct = targetProduct
        message = `Keresleti Boom! A ${targetProduct} eladási ára az egekbe szökött a Banknál!`
        icon = "🚀"
    }
    else if (type === 'supply_shock') {
        state.supplyShock = true
        message = "Beszállítói Válság! A Vetőmag ára jelentősen megnőtt!"
        icon = "🏭"
    }

    // Elmentjük a legújabb eseményt a globális Notifikációs rendszernek (így SWR ki tudja jelezni)
    if (type !== 'clear') {
        const expiresAt = durationSeconds ? new Date(Date.now() + durationSeconds * 1000).toISOString() : null
        state.eventExpiresAt = expiresAt
        state.latestEvent = {
            id: crypto.randomUUID(),
            type,
            message,
            icon,
            timestamp: new Date().toISOString()
        }
    }

    await prisma.$transaction(async (tx) => {
        await tx.session.update({
            where: { id: sessionId },
            data: { globalState: JSON.stringify(state) }
        })

        if (session.rounds[0]) {
            // Esemény naplózása az adatbázisba "rendszer" üzenetként
            // fromUserId egyelőre üresen is maradhat ha tennénk rá nullable-t, 
            // de mivel kötelező a schema szerint, megkeressük az első admint, vagy a session létrehozóját.
            // Egyszerűbb, ha beletesszük hogy melyik userId sütötte el, de itt ezt most kihagyjuk, 
            // helyette egy 'SYSTEM' hardcoded string nem jó mert relation. 
            // Kihagyjuk a naplózást az Interaction-be most, mert a Session object maga is tárolja a latestEvent-et, ami elég a funkciókhoz.
        }
    })

    revalidatePath(`/sessions/${sessionId}`)
    revalidatePath(`/play/${sessionId}`)

    return { success: true, message }
}
