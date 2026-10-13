# Pincer AI — Phase 2: Classic Rules Specification and Playable Game Engine

We now have two sources of rules:
1. The previously supplied "Turn Cards: A Quick Rule Reference While Playing".
2. A full transcript of the developer's rule overview video, describing the "classic rules".

The video transcript is the primary source for the initial Classic Rules implementation. The quick reference is a secondary source. Do not silently merge conflicting rules.

## Step 1 — Inspect the existing project

Before changing anything:
- Inspect the repository structure and existing implementation.
- Read the README, rule specification, open questions, and tests.
- Run the existing test suite.
- Identify what is implemented, incomplete, inconsistent, or missing.
- Preserve working code and avoid unnecessary rewrites.

Produce a concise implementation report before proceeding.

## Step 2 — Create a versioned rules specification

Create `docs/classic_rules.md` and update `docs/open_questions.md`.

Record the following confirmed Classic Rules:

### Setup
- The physical game contains 58 terrain tiles.
- Six terrain/resource categories are described: wheat, woods, hills, mountains, stone, and water.
- Each player starts with one colony and one musketeer.
- Colonies must be at least three tiles apart.
- Colonies cannot be built on edge tiles.
- The actual board layout and exact setup procedure are not yet specified.

### Turn sequence
1. Harvest: roll the six-sided resource die. Every eligible colony produces one resource card matching the result, subject to enemy occupation.
2. Mobilization: move units and conduct attacks.
3. Development: spend resource cards to construct infrastructure and recruit units.
4. Newly purchased units cannot act until their next eligible turn.

### Movement and combat
- One unit per tile.
- Land units cannot enter mountain or water tiles.
- Musketeer: movement and attack range of one tile.
- Cavalry: movement and attack range of two tiles.
- Cannon: movement range of one tile, attack range of one tile, with an immediate retreat after attacking.
- Frigate: naval unit with an attack range of two tiles; it transports one land unit across water.
- When a unit attacks, the defender's piece is removed and the attacker occupies its tile.
- The defender can make one immediate counter-move or counter-attack before the attacking player's turn resumes.
- Frigates can blockade enemy harbors.

### Infrastructure and costs

Implement the costs below only where the resource terminology is unambiguous:

- Colony: 2 wood, 2 wheat, 1 stone, 1 iron ore.
- Wall: 3 stone.
- Harbor: 2 wood, 1 iron ore.
- Bridge: 1 stone per bridge piece.
- Musketeer: 2 wheat or 2 fish.
- Cavalry: 2 wheat and 1 "Mustang" card.
- Cannon: 4 iron ore.
- Frigate: 2 wood and 2 iron ore.

Important: the video transcript may contain speech-to-text errors. The six terrain categories do not clearly establish how "fish", "Mustang", and "iron ore" map to the resource cards. Do not guess these mappings. Make the resource catalog configurable and document the unresolved mappings.

### Infrastructure mechanics
- Colonies collect resources from adjacent terrain and unlock musketeer recruitment.
- Harbors are built on water tiles adjacent to colonies, unlock frigate recruitment, and reduce the exchange rate by one.
- Walls surround existing colonies and unlock cannon recruitment.
- Roads connect colonies, reduce the exchange rate for each connected colony, unlock cavalry recruitment, and allow land units to transfer between connected colonies in one move.
- Bridges cross water between land on both sides and allow land units to cross.

### Victory
The classic video describes victory as controlling four colonies, approximately three quarters of the board's colonies. The precise victory interpretation and the number of colonies required under every board configuration are unresolved.

Implement a configurable victory rule. Use four controlled colonies as the provisional Classic Rules threshold, but do not hard-code assumptions about board saturation or elimination.

## Step 3 — Implement the next playable vertical slice

After the specification is written, implement the following in order:

1. Configurable terrain/resource catalog.
2. Board graph, terrain restrictions, and colony spacing.
3. Player state, colony ownership, units, and resource-card inventories.
4. Harvest phase with seeded dice rolls.
5. Legal movement generation for all four unit types.
6. Basic attacks and immediate counter-moves.
7. Development actions and configurable construction costs.
8. End-of-turn processing and delayed unit activation.
9. A complete legal-action loop for two players.
10. A basic random bot for each player.

Keep maneuver cards, advanced blockade details, and other ambiguous mechanics disabled or explicitly marked as incomplete until their rules are clarified.

## Step 4 — Testing requirements

Use pytest and add tests for:
- Terrain movement restrictions.
- Colony spacing and edge restrictions.
- Resource harvesting.
- Construction costs and placement conditions.
- Unit movement ranges.
- Attack, capture, and counter-move sequences.
- Cannons returning after attacks.
- Newly purchased units being inactive until their next eligible turn.
- Road-connected movement.
- Victory detection.
- Invalid actions leaving the state unchanged.

Use a small synthetic board for tests. Clearly distinguish it from the real 58-tile board.

## Step 5 — Deliverables

At the end, provide:
- The files changed.
- Tests executed and their results.
- A list of implemented rules.
- A list of unresolved rules.
- Instructions for running an automated game between two random bots.

Do not implement minimax or MCTS yet. First make the game engine reliable enough to simulate complete games.