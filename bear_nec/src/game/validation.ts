import { Tableau, GridPosition } from './types';

/**
 * Checks whether the given coordinates fall within the 3x4 grid bounds.
 */
export function isInBounds(row: number, col: number): boolean {
  return row >= 0 && row < 3 && col >= 0 && col < 4;
}

/**
 * Creates a fresh empty 3x4 tableau (3 rows by 4 columns).
 */
export function createEmptyTableau(): Tableau {
  return [
    [null, null, null, null],
    [null, null, null, null],
    [null, null, null, null],
  ];
}

/**
 * Counts the number of placed cards in the tableau.
 */
export function countTableauCards(tableau: Tableau): number {
  let count = 0;
  for (const row of tableau) {
    for (const cell of row) {
      if (cell !== null) {
        count++;
      }
    }
  }
  return count;
}

/**
 * Validates whether placing a card at (row, col) is legal according to Bear Necessities rules:
 * 1. Coordinates must be within grid boundaries.
 * 2. Slot must currently be empty.
 * 3. First card in tableau: any position (0..2, 0..3) is valid.
 * 4. Subsequent cards: must be orthogonally adjacent to at least one existing card.
 * 5. Bounding box rule: all placed cards (including the new card) must fit within a
 *    4-column by 3-row bounding box:
 *    (maxCol - minCol + 1 <= 4) && (maxRow - minRow + 1 <= 3).
 */
export function isValidPlacement(tableau: Tableau, row: number, col: number): boolean {
  const rowCount = tableau.length;
  if (rowCount === 0) return false;
  const colCount = tableau[0].length;

  // 1. Grid boundary check
  if (row < 0 || row >= rowCount || col < 0 || col >= colCount) {
    return false;
  }

  // 2. Slot must be empty
  if (tableau[row][col] !== null) {
    return false;
  }

  // Collect all currently placed cards
  const placed: GridPosition[] = [];
  for (let r = 0; r < rowCount; r++) {
    for (let c = 0; c < colCount; c++) {
      if (tableau[r][c] !== null) {
        placed.push({ row: r, col: c });
      }
    }
  }

  // 3. First card placement: any empty position within bounds is valid
  if (placed.length === 0) {
    return true;
  }

  // 4. Must be orthogonally adjacent to at least one existing card
  const isAdjacent = placed.some(
    (p) => Math.abs(p.row - row) + Math.abs(p.col - col) === 1
  );
  if (!isAdjacent) {
    return false;
  }

  // 5. Must obey 4-column by 3-row bounding box constraint
  const allRows = [...placed.map((p) => p.row), row];
  const allCols = [...placed.map((p) => p.col), col];

  const minRow = Math.min(...allRows);
  const maxRow = Math.max(...allRows);
  const minCol = Math.min(...allCols);
  const maxCol = Math.max(...allCols);

  const height = maxRow - minRow + 1;
  const width = maxCol - minCol + 1;

  if (height > 3 || width > 4) {
    return false;
  }

  return true;
}

/**
 * Returns all valid placement positions in the tableau.
 */
export function getValidPlacements(tableau: Tableau): GridPosition[] {
  const valid: GridPosition[] = [];
  for (let r = 0; r < tableau.length; r++) {
    for (let c = 0; c < tableau[r].length; c++) {
      if (isValidPlacement(tableau, r, c)) {
        valid.push({ row: r, col: c });
      }
    }
  }
  return valid;
}
