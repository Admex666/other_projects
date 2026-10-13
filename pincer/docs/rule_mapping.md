# Rule-to-Code Traceability Matrix

This document maps each rule in `docs/spec/player_card.md` to its implementation in the codebase.

| Rule in Quick Reference | Implementation Location | Logic & Invariants |
| :--- | :--- | :--- |
| **Annexing Colonies: Occupation** | `pincer.entities.colony.Colony`, `pincer.engine.colony_manager` | `Colony.current_occupant` tracks current occupant. If different from `original_owner`, colony is annexed. |
| **Annexing Colonies: Harvest collection** | `pincer.engine.harvest_manager` | Resources rolled for an annexed colony are credited to `Colony.controller` (`current_occupant`). |
| **Annexing Colonies: Unit recruitment prohibition** | `pincer.actions.recruit_unit` | Annexed colonies cannot recruit land/naval units (`colony.is_annexed` blocks recruitment). |
| **Annexing Colonies: Port trade bonus & construction** | `pincer.actions.build_port`, `pincer.entities.player` | Occupier gets trade bonus from existing port. Can build port in colony's color. |
| **Annexing Colonies: Loss of road bonuses** | `pincer.board.road_network` | Roads connected to annexed colony do not count toward road connectivity bonus for either player. |
| **Annexing Colonies: Reversion upon vacancy** | `pincer.engine.turn_manager` | When occupying unit leaves tile, ownership reverts to `original_owner` on their turn; occupant fort destroyed. |
| **Phase I: Harvest Die Roll** | `pincer.cards.dice.DiceRoller`, `pincer.engine.harvest_manager` | Die rolls resource/value; each colony checks adjacent tiles for match; blocked if enemy unit on adjacent tile. |
| **Phase II: Mobilization Movement** | `pincer.actions.move_unit`, `pincer.engine.movement_validator` | Units move up to range; new units (`built_turn == current_turn`) blocked from moving. |
| **Phase II: Combat & Capture** | `pincer.actions.attack`, `pincer.engine.combat_resolver` | Attacker enters enemy tile; defender piece removed; enters `CounterMoveState`. |
| **Phase II: Counter-move Tracking** | `pincer.state.counter_move`, `pincer.engine.combat_resolver` | Defender must use separate piece for each counter-move until exhausted before reusing. |
| **Phase III: Development Trading** | `pincer.actions.trade`, `pincer.entities.player` | 5:1 base rate, reduced by 1 per port or connected colony down to 2:1. |
| **Phase III: Infrastructure Building** | `pincer.actions.build_*`, `pincer.engine.infrastructure_validator` | Configurable resource costs validated before deduction. |
| **Colony Placement Rules** | `pincer.board.board_graph.is_valid_colony_placement` | Tile occupied by friendly unit; graph distance $\ge 3$ from any existing colony; not an edge tile. |
| **Port Placement Rules** | `pincer.actions.build_port` | Water tile adjacent to friendly colony. Allows frigate purchase; trade bonus unless enemy naval present. |
| **Fort Placement & Defense** | `pincer.actions.build_fort`, `pincer.engine.combat_resolver` | Built on colony; allows cannons; blocks direct attack unless enemy has cannon/frigate + adjacent land unit. |
| **Roads & Bridges** | `pincer.board.road_network`, `pincer.actions.build_road` | Roads along tile edges; bridges across water touching land on both sides; 1-move unit transfer between connected colonies. |
| **Musketeer Rules** | `pincer.entities.units.Musketeer` | Move/attack 1 tile; land only (no mountains); placed in empty, friendly colony. |
| **Cavalry Rules** | `pincer.entities.units.Cavalry` | Move/attack 2 tiles; cannot cross enemy tiles or mountains; requires road connection between colonies. |
| **Cannon Rules** | `pincer.entities.units.Cannon` | Move/attack 1 tile; may return immediately to original tile after attack; MUST return if attacking naval unit; requires fort to recruit. |
| **Frigate Rules** | `pincer.entities.units.Frigate` | Water only; move 1-2 tiles; transports 1 land unit; unit lost on frigate defeat; placed in empty, friendly port. |
| **Maneuver: Ambush** | `pincer.cards.maneuvers` | Played before attacking; prevents opponent counter card. |
| **Maneuver: Outflank** | `pincer.cards.maneuvers` | Played before move/attack; allows 1 extra move/attack with same unit. |
| **Maneuver: Retreat** | `pincer.cards.maneuvers` | Played when attacked; moves attacked unit into empty tile within range instead of being captured. |
| **Maneuver: Fortify** | `pincer.cards.maneuvers` | Played when attacked; deflects attack; both units remain on original tiles. |
| **Maneuver: Encirclement** | `pincer.cards.maneuvers` | Played before move/attack; 2 consecutive moves/attacks with separate units; skips opponent counter-move. |
| **Victory: Domination** | `pincer.victory.domination` | Board fully colonized (no valid colony location left) AND player controls $\ge 75\%$ of all colonies. |
