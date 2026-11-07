# PROJECT HANDOVER — Bear Necessities: Private Online Multiplayer Implementation

## 1. Project overview

Build a private, browser-based digital implementation of the board game **Bear Necessities**, published by Mojito Studios.

### The original idea

I want to recreate Bear Necessities as a playable online game because there is currently no convenient way for my girlfriend and me to play it together outside Board Game Arena (BGA).

The goal is to build our own lightweight, private multiplayer web application where two players can connect through a shared room link and play the original game remotely.

This is primarily a personal, non-commercial project.

**Important:** The goal is to faithfully reproduce the original gameplay, rules, card effects, scoring, and turn structure — not to create a loosely inspired alternative.

The application should feel polished, intuitive, responsive, and enjoyable to use.

## 2. Source materials

Two important source files are available:

### Official rulebook (PDF)
https://www.mojitostudios.com/assets/files/bear-necessities/Bear%20Necessities%20Rules%20LQ.pdf

Use this as the primary source of truth for:
- Game setup
- Rules
- Turn structure
- Card effects
- Scoring
- End-game conditions
- Special cases

Read and understand the entire document before implementing the game engine.

### Board Game Arena card spritesheet
https://x.boardgamearena.net/data/themereleases/current/games/bearnecessities/261001-1012/img/cards.jpg

This is a candidate visual reference containing the game's card artwork.

Investigate the image:
- Download and inspect its dimensions.
- Determine the card layout and grid structure.
- Identify individual card boundaries.
- Determine whether there are additional visual states or card backs.
- Determine whether all cards are represented.
- Create a mapping between card artwork and the card definitions in the rulebook.

**Intellectual property constraint:** The spritesheet is hosted by BGA and may contain copyrighted artwork. Do not assume that public accessibility grants permission to reuse, redistribute, or embed it in a separate application. Investigate licensing and permissions. Keep the asset extraction and rendering pipeline modular so that authorized replacement artwork can be substituted without changing the game engine. Do not publish or distribute copyrighted assets without authorization.

## 3. First task: Research and reverse engineering

Do not start by immediately writing the entire application.

First, investigate the source materials and produce a structured understanding of the game.

### Deliverables

1. Extract the rulebook's complete rules into structured notes.
2. Identify all card types and card effects.
3. Determine the exact number of cards. Note any discrepancies between different sources.
4. Inspect the spritesheet and determine its structure.
5. Create a card inventory with:
   - Unique card ID
   - Card name, if available
   - Card type
   - Card properties
   - Scoring/effect description
   - Artwork reference
6. Identify ambiguities and missing information.

Do not invent missing card effects or rules.

If something cannot be determined from the provided materials, explicitly flag it for investigation.

## 4. Game implementation requirements

### Multiplayer

The application must support two remote players.

Requirements:
- Create a private game room.
- Generate a shareable invitation URL.
- Allow a second player to join using that URL.
- Synchronize both players' game states in real time.
- Ensure players only see information they are supposed to see.
- Handle player disconnections and reconnections.
- Prevent conflicting actions and duplicate moves.
- Support starting a new game and rematches.

A simple room-based multiplayer architecture is sufficient. Do not build unnecessary social features, accounts, or matchmaking.

### Gameplay

Implement the original game faithfully.

The game engine should handle:
- Game initialization
- Deck creation and shuffling
- Card distribution
- Player turns
- Card selection
- Card placement
- Card effects
- Any special card interactions
- Scoring
- Round progression
- End-game conditions
- Winner determination

All game rules should live in a separate, testable game-engine module rather than being scattered throughout UI components.

The server must be authoritative for game state and validate every player action.

Never trust client-side calculations for scoring or game progression.

### User interface

Build a clean, modern interface with a warm woodland / forest-inspired visual identity.

The interface should prioritize usability over unnecessary decoration.

Required elements:
- Game room / lobby
- Player information
- Individual player boards
- Card display
- Card selection and placement interactions
- Current turn indicator
- Game progress indicator
- Score display
- Game-end screen
- Rematch button

The interface must be responsive and work on desktop and mobile.

### Visual design

Use the original card artwork only if its use is authorized.

If it is not authorized, create a modular visual asset system that supports original replacement artwork.

Do not generate substitute artwork for all cards before the card inventory and mechanics are understood.

The card rendering component should receive structured card data and artwork references, making it easy to replace the entire visual layer later.

## 5. Suggested technical architecture

Choose a pragmatic stack that allows fast development without sacrificing reliability.

Suggested stack:

- Frontend: React + TypeScript
- Build tool: Vite or an equivalent modern setup
- Styling: Tailwind CSS
- Multiplayer/backend: Supabase Realtime + PostgreSQL, or a lightweight WebSocket server
- Deployment: Vercel for frontend and an appropriate backend hosting solution

You may choose alternatives if there is a clear technical advantage.

Keep the architecture simple.

### Suggested project structure

- `src/game/` — game engine and rules
- `src/game/cards/` — card definitions and metadata
- `src/game/scoring/` — scoring logic
- `src/components/` — UI components
- `src/pages/` — application pages
- `src/realtime/` — multiplayer communication
- `src/server/` — authoritative game logic, if applicable
- `public/assets/cards/` — authorized card assets

## 6. Testing requirements

Correct gameplay is more important than visual polish.

Create automated tests for:

- Deck construction
- Deck shuffling and distribution
- Valid and invalid moves
- Card effects
- Turn progression
- Scoring
- End-game conditions
- Edge cases
- Multiplayer synchronization

Where possible, derive expected test cases directly from the rulebook.

Create deterministic game-engine tests using fixed decks and controlled player actions.

Do not rely exclusively on manually playing the game to verify correctness.

## 7. Development workflow

Work incrementally.

### Phase 1 — Research
- Read the PDF.
- Inspect the spritesheet.
- Build the card inventory.
- Document the rules.
- Identify unresolved questions.

### Phase 2 — Game engine
- Implement the rules independently of the UI.
- Create automated tests.
- Verify scoring and special interactions.

### Phase 3 — Single-player prototype
- Build the game board.
- Implement card selection and placement.
- Make the game playable locally with two simulated players.

### Phase 4 — Multiplayer
- Implement room creation.
- Add invitation links.
- Synchronize game state.
- Handle reconnects and invalid actions.

### Phase 5 — Polish
- Improve animations and transitions.
- Add clear game feedback.
- Optimize desktop and mobile layouts.
- Test a complete game from start to finish.

## 8. Important engineering principles

1. Correct rules before beautiful UI.
2. Keep the game engine independent of the frontend.
3. Use TypeScript types for cards, players, game states, and actions.
4. Keep all card definitions in structured data, not hardcoded UI logic.
5. Make scoring deterministic and testable.
6. Make the server authoritative.
7. Avoid overengineering.
8. Do not introduce unnecessary features outside the original scope.
9. Document assumptions and unresolved questions.
10. Do not silently make up rules.

## 9. Definition of done

The project is complete when:

- Two players can open a shared URL and join the same private room.
- Both players can play a complete game remotely.
- All original card mechanics are implemented.
- Scoring matches the official rules.
- The game handles disconnections and reconnections.
- The UI works on desktop and mobile.
- A rematch can be started without creating a new room.
- Automated tests cover the core game mechanics.

## 10. Your first response and immediate actions

Before implementing anything substantial:

1. Confirm that you can access the PDF and spritesheet.
2. Summarize your understanding of the game.
3. Report the spritesheet dimensions and apparent card layout.
4. Present the proposed card data structure.
5. List any missing information or ambiguities.
6. Recommend the final technical architecture.

Then proceed with implementation in small, verifiable increments.

**Do not stop after producing a plan.** Once the initial research is complete and any blocking questions are identified, continue implementing the project autonomously wherever possible.

The ultimate goal is simple: my girlfriend and I should be able to open a link, join the same room, and play Bear Necessities together.