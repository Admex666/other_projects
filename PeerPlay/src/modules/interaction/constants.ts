// Define product production requirements and outputs based on Agriculture theme
export const PRODUCTION_RECIPES = {
    wheat: { name: 'Búza', rawCost: 1, techReq: 1, baseValue: 100, baseTime: 30 },
    corn: { name: 'Kukorica', rawCost: 2, techReq: 2, baseValue: 250, baseTime: 60 },
    sunflower: { name: 'Napraforgó', rawCost: 1, techReq: 3, baseValue: 180, baseTime: 45 },
    wine: { name: 'Bor', rawCost: 3, techReq: 4, baseValue: 400, baseTime: 75 },
}

export type ProductType = keyof typeof PRODUCTION_RECIPES
