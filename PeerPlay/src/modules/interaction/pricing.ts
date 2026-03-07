'use server'

import prisma from '@/lib/prisma'
import { PRODUCTION_RECIPES, ProductType } from './constants'
import { BANK_BUY_MARKUP } from './bankConstants'

/**
 * Kereslet-kínálat alapú árazás:
 * Ha a session 2. körös vagy afelett van, a Bank inventory-ja módosítja az árakat.
 * - quantity: a Banknál lévő darabszám. Pozitív ha sokat vett a játékosoktól, negatív ha sokat adott el nekik.
 * - ha a quantity nő (sok az eladás), a banki vételi/eladási ár csökken.
 * - ha a quantity csökken (sok a vásárlás), az ár nő.
 */
export async function getDynamicPricing(sessionId: string) {
    const session = await prisma.session.findUnique({
        where: { id: sessionId },
        include: { bankInventories: true }
    })

    if (!session) throw new Error("Session nem található")

    const roundData = session.currentRound
    const globalState = JSON.parse(session.globalState || '{}')

    let isEventActive = true
    if (globalState.eventExpiresAt && new Date(globalState.eventExpiresAt) <= new Date()) {
        isEventActive = false
    }

    // Base multipliers
    let globalMultiplier = 1.0

    // Események: Piac-összeomlás minden termék értékét felezi
    if (isEventActive && globalState.marketCrash) {
        globalMultiplier = 0.5
    }

    const prices: Record<string, { sellToBank: number, buyFromBank: number, bankInventory: number }> = {}

    const itemsToPrice = [
        ...Object.entries(PRODUCTION_RECIPES).map(([key, recipe]) => ({ key, baseValue: recipe.baseValue, type: 'product' as const })),
        { key: 'rawMaterial', baseValue: 38, type: 'raw' as const } // ~50 HUF base buy price
    ]

    for (const item of itemsToPrice) {
        const productKey = item.key
        const bankInv = session.bankInventories.find(b => b.productKey === productKey)?.quantity || 0

        // Alap árak + Piac-összeomlás hatása
        let baseValue = item.baseValue * globalMultiplier

        // Események: Beszállítói Válság (Dula rawMaterial ár)
        if (isEventActive && globalState.supplyShock && item.type === 'raw') {
            baseValue = baseValue * 2.0
        }

        // Események: Bumm! Egyetlen termék ára megduplázódik (eladásra nagyon sokat fizet a bank)
        if (isEventActive && globalState.boomProduct === productKey && item.type === 'product') {
            baseValue = baseValue * 2.0
        }

        // Dinamikus ár: 2. körtől él a kereslet-kínálat.
        // Koncepció: minden 5 darab után (vagy terméktől függően) 10%-ot mozdul el az ár?
        // Finomhangolás: Minél drágább valami (pl. Bor), annál hamarabb mozdul az ára kis mennyiségre is.
        // Hogy egyszerű legyen: "elasticity" = 100 / baseValue. (Búza=100 -> 1, Bor=400 -> 0.25)
        if (roundData >= 2) {
            // formula: price = base * (0.95 ^ (quantity / weight)), ahol a weight mondjuk 3.
            // Magyarul: ha 3 Búzát eladnak a banknak, az ár ~5%-ot esik.
            // Ha -3 Búzája van a banknak (vásároltak tőle), felmegy ~5%-ot.
            const weight = 3
            const modifier = Math.pow(0.95, bankInv / weight)
            baseValue = baseValue * modifier

            // Padló / Plafon védelmek (ne menjen be 0 alá, ne menjen fel csillagokba hirtelen)
            if (baseValue < item.baseValue * 0.2) baseValue = item.baseValue * 0.2
            if (baseValue > item.baseValue * 3.0) baseValue = item.baseValue * 3.0
        }

        // Eladási ár amit a Bank AD érte -> (baseValue)
        const sellToBankPrice = Math.round(baseValue)
        // Vételi ár amennyiért a Bank ADJA -> (baseValue * markup)
        const buyFromBankPrice = Math.round(baseValue * BANK_BUY_MARKUP)

        prices[productKey] = {
            sellToBank: sellToBankPrice,
            buyFromBank: buyFromBankPrice,
            bankInventory: bankInv
        }
    }

    return prices
}
