import {
  CardDefinition,
  CardColor,
  CardType,
  GridPosition,
  Tableau,
  PlayerState,
  ActivationContext,
} from '../types';

/**
 * Validates whether a row and col coordinate is within the 3x4 grid bounds.
 */
export function isInBounds(row: number, col: number): boolean {
  return row >= 0 && row < 3 && col >= 0 && col < 4;
}

/**
 * Returns the orthogonal neighbors (up, down, left, right) of a given cell that contain cards.
 * Supports both (tableau, pos) and (tableau, row, col) call signatures.
 */
export function getOrthogonalNeighbors(
  tableau: Tableau,
  posOrRow: GridPosition | number,
  col?: number
): { card: CardDefinition; pos: GridPosition }[] {
  const row = typeof posOrRow === 'number' ? posOrRow : posOrRow.row;
  const c = typeof posOrRow === 'number' ? (col as number) : posOrRow.col;
  const pos: GridPosition = { row, col: c };

  const neighbors: { card: CardDefinition; pos: GridPosition }[] = [];
  const directions = [
    { r: -1, c: 0 },
    { r: 1, c: 0 },
    { r: 0, c: -1 },
    { r: 0, c: 1 },
  ];

  for (const dir of directions) {
    const nr = pos.row + dir.r;
    const nc = pos.col + dir.c;
    if (nr >= 0 && nr < tableau.length && nc >= 0 && nc < tableau[0].length) {
      const neighborCard = tableau[nr][nc];
      if (neighborCard !== null) {
        neighbors.push({ card: neighborCard, pos: { row: nr, col: nc } });
      }
    }
  }

  return neighbors;
}

/**
 * Returns all non-null cards currently placed in the tableau.
 */
export function getAllCardsInTableau(tableau: Tableau): { card: CardDefinition; pos: GridPosition }[] {
  const cards: { card: CardDefinition; pos: GridPosition }[] = [];
  for (let r = 0; r < tableau.length; r++) {
    for (let c = 0; c < tableau[r].length; c++) {
      const card = tableau[r][c];
      if (card !== null) {
        cards.push({ card, pos: { row: r, col: c } });
      }
    }
  }
  return cards;
}

/**
 * Finds the size of the largest orthogonally connected component of cards matching a target name.
 */
export function findLargestConnectedGroup(tableau: Tableau, targetName: string): number {
  const rowCount = tableau.length;
  const colCount = tableau[0].length;
  const visited: boolean[][] = Array.from({ length: rowCount }, () =>
    Array(colCount).fill(false)
  );

  let maxSize = 0;

  for (let r = 0; r < rowCount; r++) {
    for (let c = 0; c < colCount; c++) {
      const card = tableau[r][c];
      if (card && card.name === targetName && !visited[r][c]) {
        // BFS for connected component
        let size = 0;
        const queue: [number, number][] = [[r, c]];
        visited[r][c] = true;

        while (queue.length > 0) {
          const [currR, currC] = queue.shift()!;
          size++;

          const dirs = [
            [-1, 0],
            [1, 0],
            [0, -1],
            [0, 1],
          ];
          for (const [dr, dc] of dirs) {
            const nr = currR + dr;
            const nc = currC + dc;
            if (
              nr >= 0 &&
              nr < rowCount &&
              nc >= 0 &&
              nc < colCount &&
              !visited[nr][nc] &&
              tableau[nr][nc]?.name === targetName
            ) {
              visited[nr][nc] = true;
              queue.push([nr, nc]);
            }
          }
        }

        if (size > maxSize) {
          maxSize = size;
        }
      }
    }
  }

  return maxSize;
}

/**
 * Evaluates the Victory Points gained when a card is activated.
 */
export function evaluateCardActivation(
  card: CardDefinition,
  tableau: Tableau,
  pos: GridPosition,
  playerState: PlayerState,
  opponentState?: PlayerState,
  context?: ActivationContext
): number {
  const effect = card.effect;
  if (!effect) {
    return 0;
  }

  const neighbors = getOrthogonalNeighbors(tableau, pos);
  const allCards = getAllCardsInTableau(tableau);

  switch (effect.type) {
    case 'adjacent_family': {
      const parents = (effect.parents as string[]) || [];
      const hasParent = neighbors.some((n) => parents.includes(n.card.name));
      return hasParent ? (effect.points as number) : (context?.isPlacement ? 1 : 0);
    }

    case 'largest_group': {
      const targetName = (effect.targetName as string) || 'Fish';
      const pointsPerCard = (effect.pointsPerCard as number) || 2;
      const groupSize = findLargestConnectedGroup(tableau, targetName);
      return groupSize * pointsPerCard;
    }

    case 'adjacent_exact_color': {
      const colors = (effect.colors as CardColor[]) || (effect.color ? [effect.color as CardColor] : []);
      const count = neighbors.filter((n) => colors.includes(n.card.color)).length;
      return count === (effect.count as number) ? (effect.points as number) : 0;
    }

    case 'adjacent_min_color': {
      const targetColor = effect.color as CardColor;
      const minCount = (effect.minCount as number) || 1;
      const count = neighbors.filter((n) => n.card.color === targetColor).length;
      if (card.hasGoal) {
        return count >= minCount
          ? (effect.metPoints as number)
          : (effect.unmetPoints as number);
      }
      return count >= minCount ? (effect.points as number) : 0;
    }

    case 'row_col_color': {
      const targetColor = effect.color as CardColor;
      const pointsPerCard = (effect.pointsPerCard as number) || 2;

      // Cards in row and column, pos counted only once
      const matched = new Set<string>();
      for (let c = 0; c < tableau[pos.row].length; c++) {
        const cd = tableau[pos.row][c];
        if (cd && cd.color === targetColor) {
          matched.add(`${pos.row},${c}`);
        }
      }
      for (let r = 0; r < tableau.length; r++) {
        const cd = tableau[r][pos.col];
        if (cd && cd.color === targetColor) {
          matched.add(`${r},${pos.col}`);
        }
      }

      return matched.size * pointsPerCard;
    }

    case 'activate_remote': {
      return (effect.points as number) || 3;
    }

    case 'tableau_type_count': {
      const targetType = effect.targetType as CardType;
      const pointsPerMatch = (effect.pointsPerMatch as number) || 1;
      const count = allCards.filter((c) => c.card.types.includes(targetType)).length;
      return count * pointsPerMatch;
    }

    case 'goal_majority_type_color': {
      // Goal: 20 VP if at least 5 of same color or type; else 2 VP
      const minCount = (effect.minCount as number) || 5;
      const colorCounts: Record<string, number> = {};
      const typeCounts: Record<string, number> = {};

      for (const item of allCards) {
        colorCounts[item.card.color] = (colorCounts[item.card.color] || 0) + 1;
        for (const t of item.card.types) {
          typeCounts[t] = (typeCounts[t] || 0) + 1;
        }
      }

      const hasFiveColor = Object.values(colorCounts).some((cnt) => cnt >= minCount);
      const hasFiveType = Object.values(typeCounts).some((cnt) => cnt >= minCount);

      if (hasFiveColor || hasFiveType) {
        return (effect.metPoints as number) || 20;
      }
      return (effect.unmetPoints as number) || 2;
    }

    case 'opponent_tableau_color': {
      const color = effect.color as CardColor;
      const pointsPerCard = (effect.pointsPerCard as number) || 2;
      if (!opponentState) return 0;
      const oppCards = getAllCardsInTableau(opponentState.tableau);
      const count = oppCards.filter((c) => c.card.color === color).length;
      return count * pointsPerCard;
    }

    case 'adjacent_color_count': {
      const targetColor = effect.color as CardColor;
      const pointsPerCard = (effect.pointsPerCard as number) || 2;
      const count = neighbors.filter((n) => n.card.color === targetColor).length;
      return count * pointsPerCard;
    }

    case 'adjacent_type_count': {
      const targetType = effect.targetType as CardType;
      const pointsPerCard = (effect.pointsPerCard as number) || 2;
      const count = neighbors.filter((n) => n.card.types.includes(targetType)).length;
      return count * pointsPerCard;
    }

    case 'adjacent_hive_count': {
      const pointsPerHive = (effect.pointsPerHive as number) || 4;
      const hiveCount = neighbors.reduce((acc, n) => acc + n.card.beeHives, 0);
      return hiveCount * pointsPerHive;
    }

    case 'adjacent_distinct_colors': {
      const requiredCount = effect.requiredCount as number;
      const distinct = new Set(neighbors.map((n) => n.card.color));
      const met = distinct.size >= requiredCount;
      return met ? (effect.metPoints as number) : (effect.unmetPoints as number);
    }

    case 'tableau_spy_count': {
      const pointsPerSpy = (effect.pointsPerSpy as number) || 5;
      const count = allCards.filter((c) => c.card.name === 'Spy').length;
      return count * pointsPerSpy;
    }

    case 'adjacent_fish_count': {
      const pointsPerCard = (effect.pointsPerCard as number) || 4;
      const count = neighbors.filter((n) => n.card.name === 'Fish').length;
      return count * pointsPerCard;
    }

    case 'secret_honey_stash': {
      const bees = context?.isPlacement
        ? (effect.placeBees as number) || 2
        : (effect.activateBees as number) || 1;
      playerState.beeTokens += bees;
      return 0;
    }

    case 'adjacent_distinct_types': {
      const pointsPerType = (effect.pointsPerType as number) || 3;
      const types = new Set<CardType>();
      for (const n of neighbors) {
        for (const t of n.card.types) {
          types.add(t);
        }
      }
      return types.size * pointsPerType;
    }

    case 'right_adjacent': {
      const rightCol = pos.col + 1;
      const hasRight = rightCol < tableau[pos.row].length && tableau[pos.row][rightCol] !== null;
      return hasRight ? (effect.metPoints as number) : (effect.unmetPoints as number);
    }

    case 'opponent_tableau_colors': {
      const colors = (effect.colors as CardColor[]) || [];
      const pointsPerMatch = (effect.pointsPerMatch as number) || 1;
      if (!opponentState) return 0;
      const oppCards = getAllCardsInTableau(opponentState.tableau);
      const count = oppCards.filter((c) => colors.includes(c.card.color)).length;
      return count * pointsPerMatch;
    }

    case 'opponent_tableau_count': {
      const pointsPerCard = (effect.pointsPerCard as number) || 1;
      if (!opponentState) return 0;
      const oppCards = getAllCardsInTableau(opponentState.tableau);
      return oppCards.length * pointsPerCard;
    }

    case 'tableau_goal_count': {
      const pointsPerGoal = (effect.pointsPerGoal as number) || 4;
      const goalCount = allCards.filter((c) => c.card.hasGoal).length;
      if (card.hasGoal && effect.minMet !== undefined) {
        return goalCount >= (effect.minMet as number)
          ? goalCount * pointsPerGoal
          : (effect.unmetPoints as number);
      }
      return goalCount * pointsPerGoal;
    }

    case 'not_adjacent_color': {
      const avoidColor = effect.avoidColor as CardColor;
      const hasAvoid = neighbors.some((n) => n.card.color === avoidColor);
      return hasAvoid ? 0 : (effect.points as number);
    }

    case 'adjacent_exact_plant': {
      const count = neighbors.filter((n) => n.card.types.includes('plant')).length;
      return count === (effect.count as number) ? (effect.points as number) : 0;
    }

    case 'rows_below_type': {
      const targetType = effect.targetType as CardType;
      const pointsPerMatch = (effect.pointsPerMatch as number) || 4;
      let count = 0;
      for (let r = pos.row + 1; r < tableau.length; r++) {
        for (let c = 0; c < tableau[r].length; c++) {
          const cd = tableau[r][c];
          if (cd && cd.types.includes(targetType)) {
            count++;
          }
        }
      }
      return count * pointsPerMatch;
    }

    case 'rows_above_type': {
      const targetTypes = (effect.targetTypes as CardType[]) || [];
      const pointsPerMatch = (effect.pointsPerMatch as number) || 4;
      let count = 0;
      for (let r = 0; r < pos.row; r++) {
        for (let c = 0; c < tableau[r].length; c++) {
          const cd = tableau[r][c];
          if (cd && cd.types.some((t) => targetTypes.includes(t))) {
            count++;
          }
        }
      }
      return count * pointsPerMatch;
    }

    case 'not_adjacent_types': {
      const avoidTypes = (effect.avoidTypes as CardType[]) || [];
      const hasAvoid = neighbors.some((n) => n.card.types.some((t) => avoidTypes.includes(t)));
      return hasAvoid ? 0 : (effect.points as number);
    }

    case 'complete_columns': {
      const pointsPerColumn = (effect.pointsPerColumn as number) || 2;
      let completeCols = 0;
      for (let c = 0; c < tableau[0].length; c++) {
        let isColFull = true;
        for (let r = 0; r < tableau.length; r++) {
          if (tableau[r][c] === null) {
            isColFull = false;
            break;
          }
        }
        if (isColFull) completeCols++;
      }
      return completeCols * pointsPerColumn;
    }

    case 'complete_rows': {
      const pointsPerRow = (effect.pointsPerRow as number) || 3;
      let completeRows = 0;
      for (let r = 0; r < tableau.length; r++) {
        if (tableau[r].every((cell) => cell !== null)) {
          completeRows++;
        }
      }
      return completeRows * pointsPerRow;
    }

    case 'tableau_card_count': {
      const pointsPerCard = (effect.pointsPerCard as number) || 1;
      return allCards.length * pointsPerCard;
    }

    case 'tableau_color_count': {
      const targetColor = effect.targetColor as CardColor;
      const pointsPerCard = (effect.pointsPerCard as number) || 1;
      const count = allCards.filter((c) => c.card.color === targetColor).length;
      return count * pointsPerCard;
    }

    case 'row_col_type_color': {
      const targetColor = effect.color as CardColor;
      const targetType = effect.cardType as CardType;
      const pointsPerCard = (effect.pointsPerCard as number) || 2;

      const matched = new Set<string>();
      for (let c = 0; c < tableau[pos.row].length; c++) {
        const cd = tableau[pos.row][c];
        if (cd && (cd.color === targetColor || cd.types.includes(targetType))) {
          matched.add(`${pos.row},${c}`);
        }
      }
      for (let r = 0; r < tableau.length; r++) {
        const cd = tableau[r][pos.col];
        if (cd && (cd.color === targetColor || cd.types.includes(targetType))) {
          matched.add(`${r},${pos.col}`);
        }
      }
      return matched.size * pointsPerCard;
    }

    case 'flat_vp': {
      return (effect.points as number) || 0;
    }

    case 'adjacent_min_city': {
      const minCount = (effect.minCount as number) || 2;
      const count = neighbors.filter((n) => n.card.color === 'city').length;
      return count >= minCount ? (effect.metPoints as number) : (effect.unmetPoints as number);
    }

    case 'tableau_hive_cards': {
      const pointsPerCard = (effect.pointsPerCard as number) || 2;
      const count = allCards.filter((c) => c.card.beeHives > 0).length;
      return count * pointsPerCard;
    }

    case 'tableau_other_bearfolk': {
      const pointsPerBearfolk = (effect.pointsPerBearfolk as number) || 2;
      const otherBearfolk = allCards.filter(
        (c) => c.card.types.includes('bearfolk') && !(c.pos.row === pos.row && c.pos.col === pos.col)
      ).length;
      return otherBearfolk * pointsPerBearfolk;
    }

    case 'goal_complete_row': {
      const isRowFull = tableau[pos.row].every((cell) => cell !== null);
      return isRowFull ? (effect.metPoints as number) : (effect.unmetPoints as number);
    }

    case 'goal_complete_col': {
      let isColFull = true;
      for (let r = 0; r < tableau.length; r++) {
        if (tableau[r][pos.col] === null) {
          isColFull = false;
          break;
        }
      }
      return isColFull ? (effect.metPoints as number) : (effect.unmetPoints as number);
    }

    case 'goal_bee_tokens': {
      const minTokens = (effect.minTokens as number) || 6;
      return playerState.beeTokens >= minTokens
        ? (effect.metPoints as number)
        : (effect.unmetPoints as number);
    }

    case 'tableau_bearfolk_no_glasses': {
      const pointsPerMatch = (effect.pointsPerMatch as number) || 4;
      // All Bearfolk in tableau
      const count = allCards.filter((c) => c.card.types.includes('bearfolk')).length;
      return count * pointsPerMatch;
    }

    case 'row_bearfolk': {
      const pointsPerBearfolk = (effect.pointsPerBearfolk as number) || 3;
      const count = tableau[pos.row].filter((c) => c !== null && c.types.includes('bearfolk')).length;
      return count * pointsPerBearfolk;
    }

    case 'opponent_bee_tokens': {
      const pointsPerToken = (effect.pointsPerToken as number) || 2;
      const tokens = opponentState ? opponentState.beeTokens : 0;
      return tokens * pointsPerToken;
    }

    case 'adjacent_exact_rose': {
      const count = neighbors.filter((n) => n.card.types.includes('plant')).length;
      return count === (effect.count as number)
        ? (effect.metPoints as number)
        : (effect.unmetPoints as number);
    }

    case 'tableau_name_starts_s': {
      const pointsPerMatch = (effect.pointsPerMatch as number) || 2;
      const count = allCards.filter((c) => c.card.name.startsWith('S')).length;
      return count * pointsPerMatch;
    }

    case 'tableau_non_adjacent': {
      const pointsPerCard = (effect.pointsPerCard as number) || 1;
      const nonAdjacent = allCards.filter((c) => {
        if (c.pos.row === pos.row && c.pos.col === pos.col) return false;
        const dist = Math.abs(c.pos.row - pos.row) + Math.abs(c.pos.col - pos.col);
        return dist > 1;
      }).length;
      return nonAdjacent * pointsPerCard;
    }

    case 'adjacent_building_and_item': {
      const hasBuilding = neighbors.some((n) => n.card.types.includes('building'));
      const hasItem = neighbors.some((n) => n.card.types.includes('item'));
      return hasBuilding && hasItem
        ? (effect.metPoints as number)
        : (effect.unmetPoints as number);
    }

    case 'all_colors_in_tableau': {
      const colors = new Set(allCards.map((c) => c.card.color));
      return colors.size === 4 ? (effect.metPoints as number) : (effect.unmetPoints as number);
    }

    case 'tableau_min_items': {
      const minItems = (effect.minItems as number) || 3;
      const pointsPerItem = (effect.pointsPerItem as number) || 3;
      const itemCount = allCards.filter((c) => c.card.types.includes('item')).length;
      return itemCount >= minItems ? itemCount * pointsPerItem : 0;
    }

    case 'bee_tokens_count': {
      const pointsPerToken = (effect.pointsPerToken as number) || 2;
      return playerState.beeTokens * pointsPerToken;
    }

    case 'reserve_color': {
      const requiredColor = effect.requiredColor as CardColor;
      const matches = playerState.reserveCard?.color === requiredColor;
      return matches ? (effect.points as number) : 0;
    }

    case 'tableau_mountain_count': {
      const pointsPerCard = (effect.pointsPerCard as number) || 2;
      const count = allCards.filter((c) => c.card.color === 'mountain').length;
      return count * pointsPerCard;
    }

    case 'row_plants': {
      const pointsPerPlant = (effect.pointsPerPlant as number) || 4;
      const count = tableau[pos.row].filter((c) => c !== null && c.types.includes('plant')).length;
      return count * pointsPerPlant;
    }

    case 'dandelion': {
      return context?.isPlacement
        ? (effect.placeVP as number) || 7
        : (effect.activateVP as number) || 1;
    }

    case 'adjacent_min_animal': {
      const minCount = (effect.minCount as number) || 1;
      const count = neighbors.filter((n) => n.card.types.includes('animal')).length;
      return count >= minCount ? (effect.points as number) : 0;
    }

    default:
      return (effect.points as number) || 0;
  }
}

/**
 * Calculates end of game final score including bee token multipliers.
 * Total VP tokens + (Total Bee Hive symbols in 4x3 tableau * Bee tokens in reserve).
 */
export function calculateFinalScore(player: PlayerState): number {
  let beeHiveSymbols = 0;
  for (const row of player.tableau) {
    for (const cell of row) {
      if (cell) {
        beeHiveSymbols += cell.beeHives;
      }
    }
  }

  const beeBonus = beeHiveSymbols * player.beeTokens;
  return player.vpTokens + beeBonus;
}

/**
 * Legacy wrapper function returning { vp, beeTokensEarned } for backwards compatibility with hotseat.
 */
export function evaluateCardScore(
  card: CardDefinition,
  pos: GridPosition,
  tableau: Tableau,
  player: PlayerState,
  opponent?: PlayerState,
  isPlacement = false
): { vp: number; beeTokensEarned: number } {
  const prevBees = player.beeTokens;
  const vp = evaluateCardActivation(card, tableau, pos, player, opponent, { isPlacement });
  const beeTokensEarned = Math.max(0, player.beeTokens - prevBees);
  return { vp, beeTokensEarned };
}
