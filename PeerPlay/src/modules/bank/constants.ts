export type ShapeType = 'SQUARE' | 'TRIANGLE' | 'CIRCLE' | 'RECTANGLE' | 'PREMIUM_PACK'

export const BASE_PRICES: Record<ShapeType, number> = {
  SQUARE: 300,
  TRIANGLE: 150,
  CIRCLE: 250,
  RECTANGLE: 100,
  PREMIUM_PACK: 800,
}

export interface ShapeBatchItem {
  shapeType: ShapeType
  quantity: number
}
