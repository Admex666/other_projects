// Define shape production requirements and outputs based on Global Exchange rules
export const PRODUCTION_RECIPES = {
    circle: { name: 'Circle', rawCost: 1, techReq: 1, baseValue: 100 },
    triangle: { name: 'Triangle', rawCost: 2, techReq: 2, baseValue: 250 },
    square: { name: 'Square', rawCost: 1, techReq: 3, baseValue: 180 },
    hexagon: { name: 'Hexagon', rawCost: 3, techReq: 4, baseValue: 400 },
}

export type ShapeType = keyof typeof PRODUCTION_RECIPES
