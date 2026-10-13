#!/usr/bin/env python3
"""Interactive Web UI for playing Pincer against an AI bot."""
import argparse
import http.server
import json
from pathlib import Path
import sys
import threading
import urllib.parse
import webbrowser

# Ensure src/ is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from pincer.actions.harvest import HarvestRollAction
from pincer.actions.mobilization import (
    MoveUnitAction,
    AttackAction,
    CounterMoveAction,
    PassCounterMoveAction,
    EndPhaseAction,
    TransferViaRoadAction,
)
from pincer.actions.development import (
    TradeWithBankAction,
    BuildColonyAction,
    BuildPortAction,
    BuildFortAction,
    BuildRoadAction,
    BuildBridgeAction,
    RecruitUnitAction,
)
from pincer.ai.random_bot import RandomBot
from pincer.core.enums import PlayerId, TurnPhase, UnitType, ResourceType, InfrastructureType
from pincer.engine.engine import PincerEngine
from pincer.state.setup import create_classic_initial_state
from pincer.state.state import GameState


# 10-tile synthetic board coordinates
NODE_COORDS_10 = {
    "M1": {"x": 210, "y": 95},
    "E1": {"x": 105, "y": 156},
    "T1": {"x": 210, "y": 217},
    "T2": {"x": 315, "y": 156},
    "T3": {"x": 420, "y": 217},
    "E2": {"x": 525, "y": 156},
    "W1": {"x": 315, "y": 277},
    "W2": {"x": 315, "y": 398},
    "T4": {"x": 420, "y": 338},
    "E3": {"x": 525, "y": 277},
}


def get_58_tile_coords():
    row_specs = [
        (0, 2, 7), (1, 1, 7), (2, 1, 8), (3, 0, 8),
        (4, 0, 9), (5, 0, 8), (6, 1, 8), (7, 2, 7), (8, 3, 6)
    ]
    R = 40.0
    dx = 1.5 * R
    dy_row = 1.7320508 * R
    dy_offset = 0.8660254 * R
    X0 = 65.0
    Y0 = 50.0

    coords = {}
    idx = 1
    for r, c_start, c_end in row_specs:
        for c in range(c_start, c_end):
            nid = f"H{idx:02d}"
            cx = X0 + c * dx
            cy = Y0 + r * dy_row + (dy_offset if (c % 2 != 0) else 0.0)
            coords[nid] = {"x": round(cx, 1), "y": round(cy, 1)}
            idx += 1
    return coords


NODE_COORDS_58 = get_58_tile_coords()


# Global game session
class GameSession:
    def __init__(self, seed: int = 42, board_type: str = "full_58"):
        self.seed = seed
        self.board_type = board_type
        self.state: GameState = create_classic_initial_state(seed=seed, board_type=board_type)
        self.bot = RandomBot(player_id=PlayerId.PLAYER_2, seed=seed)
        board_label = "Teljes 58 mezős tábla" if board_type == "full_58" else "10 mezős teszttábla"
        self.log = [f"Játék elindult ({board_label})! Te vagy a Kék játékos (P1), a Bot a Piros (P2)."]

    def reset(self, seed: int = 42, board_type: str = "full_58"):
        self.seed = seed
        self.board_type = board_type
        self.state = create_classic_initial_state(seed=seed, board_type=board_type)
        self.bot = RandomBot(player_id=PlayerId.PLAYER_2, seed=seed)
        board_label = "Teljes 58 mezős tábla" if board_type == "full_58" else "10 mezős teszttábla"
        self.log = [f"Új játék elindítva ({board_label})!"]

    def run_bot_turns_if_needed(self):
        """Runs bot actions if it is Player 2's turn or if bot needs to counter-move."""
        bot_p = PlayerId.PLAYER_2
        max_bot_steps = 30
        steps = 0

        while steps < max_bot_steps and self.state.winner is None:
            # Check if bot needs to act
            bot_must_act = False
            if self.state.counter_move_state and self.state.counter_move_state.is_active:
                if self.state.counter_move_state.defender_player_id == bot_p:
                    bot_must_act = True
            elif self.state.current_player == bot_p:
                bot_must_act = True

            if not bot_must_act:
                break

            action = self.bot.select_action(self.state)
            action_desc = self._describe_action(action)
            PincerEngine.apply_action(self.state, action)
            self.log.append(f"[BOT] {action_desc}")
            steps += 1

    def _describe_action(self, action) -> str:
        p = action.player_id.value
        if isinstance(action, HarvestRollAction):
            return f"Kockadobás a Harvest fázisban: {self.state.last_harvest_roll}"
        if isinstance(action, MoveUnitAction):
            return f"Egység mozgása: {action.unit_id} -> {action.target_node_id}"
        if isinstance(action, AttackAction):
            return f"Támadás: {action.attacker_unit_id} -> {action.target_node_id}"
        if isinstance(action, CounterMoveAction):
            return f"Ellenlépés: {action.defender_unit_id} -> {action.target_node_id} (támadás: {action.is_attack})"
        if isinstance(action, PassCounterMoveAction):
            return f"Ellenlépés passzolva."
        if isinstance(action, BuildColonyAction):
            return f"Kolónia építése: {action.node_id}"
        if isinstance(action, BuildFortAction):
            return f"Fal/Erőd építése a kolóniára: {action.colony_id}"
        if isinstance(action, BuildPortAction):
            return f"Kikötő építése: {action.node_id}"
        if isinstance(action, RecruitUnitAction):
            return f"Új egység toborzása: {action.unit_type.value} a {action.target_node_id} mezőn"
        if isinstance(action, EndPhaseAction):
            return f"Fázis lezárása ({self.state.phase.value})"
        return str(action)


session = GameSession()


def serialize_state(state: GameState, log_messages, board_type: str = "full_58") -> dict:
    is_58 = (len(state.board.nodes) > 20)
    coords_map = NODE_COORDS_58 if is_58 else NODE_COORDS_10
    hex_radius = 38 if is_58 else 66
    view_box = "10 5 590 685" if is_58 else "10 10 610 475"

    nodes_data = []
    for nid, node in state.board.nodes.items():
        coords = coords_map.get(nid, {"x": 300, "y": 250})
        colony = state.get_colony_at(nid)
        port = state.get_port_at(nid)
        unit = state.get_unit_at(nid)
        nodes_data.append({
            "id": nid,
            "x": coords["x"],
            "y": coords["y"],
            "terrain": node.terrain.value,
            "harvest_value": node.harvest_value,
            "resource_type": node.resource_type.value if node.resource_type else None,
            "is_edge": node.is_edge,
            "colony": {
                "id": colony.colony_id,
                "owner": colony.original_owner.value,
                "occupant": colony.current_occupant.value if colony.current_occupant else None,
                "controller": colony.controller.value,
                "has_fort": colony.has_fort,
            } if colony else None,
            "port": {
                "id": port.port_id,
                "owner": port.owner_id.value,
            } if port else None,
            "unit": {
                "id": unit.unit_id,
                "type": unit.unit_type.value,
                "owner": unit.player_id.value,
                "built_turn": unit.built_turn,
                "can_act": unit.can_act_on_turn(state.turn_number),
            } if unit else None,
        })

    edges_data = []
    for eid, edge in state.board.edges.items():
        ca = coords_map.get(edge.node_a, {"x": 0, "y": 0})
        cb = coords_map.get(edge.node_b, {"x": 0, "y": 0})
        edges_data.append({
            "id": eid,
            "a": edge.node_a,
            "b": edge.node_b,
            "x1": ca["x"],
            "y1": ca["y"],
            "x2": cb["x"],
            "y2": cb["y"],
            "is_water_crossing": edge.is_water_crossing,
            "road_owner": edge.road_owner.value if edge.road_owner else None,
            "bridge_owner": edge.bridge_owner.value if edge.bridge_owner else None,
        })

    p1 = state.players[PlayerId.PLAYER_1]
    p2 = state.players[PlayerId.PLAYER_2]

    legal_actions = []
    for act in PincerEngine.get_legal_actions(state):
        if act.player_id == PlayerId.PLAYER_1:
            d = {"type": type(act).__name__, "player": act.player_id.value}
            if hasattr(act, "unit_id"):
                d["unit_id"] = act.unit_id
            if hasattr(act, "attacker_unit_id"):
                d["attacker_unit_id"] = act.attacker_unit_id
            if hasattr(act, "defender_unit_id"):
                d["defender_unit_id"] = act.defender_unit_id
            if hasattr(act, "target_node_id"):
                d["target_node_id"] = act.target_node_id
            if hasattr(act, "node_id"):
                d["node_id"] = act.node_id
            if hasattr(act, "colony_id"):
                d["colony_id"] = act.colony_id
            if hasattr(act, "unit_type"):
                d["unit_type"] = act.unit_type.value
            if hasattr(act, "edge_id"):
                d["edge_id"] = act.edge_id
            legal_actions.append(d)

    return {
        "turn": state.turn_number,
        "phase": state.phase.value,
        "current_player": state.current_player.value,
        "last_harvest_roll": state.last_harvest_roll,
        "counter_move_active": bool(state.counter_move_state and state.counter_move_state.is_active),
        "counter_move_defender": state.counter_move_state.defender_player_id.value if state.counter_move_state and state.counter_move_state.is_active else None,
        "winner": state.winner.value if state.winner else None,
        "board_type": board_type,
        "is_58": is_58,
        "hex_radius": hex_radius,
        "view_box": view_box,
        "p1": {
            "resources": {r.value: p1.resources.get(r, 0) for r in ResourceType},
            "colonies_count": len(state.get_player_colonies(PlayerId.PLAYER_1)),
            "exchange_rate": state.calculate_exchange_rate(PlayerId.PLAYER_1),
        },
        "p2": {
            "resources": {r.value: p2.resources.get(r, 0) for r in ResourceType},
            "colonies_count": len(state.get_player_colonies(PlayerId.PLAYER_2)),
            "exchange_rate": state.calculate_exchange_rate(PlayerId.PLAYER_2),
        },
        "nodes": nodes_data,
        "edges": edges_data,
        "legal_actions": legal_actions,
        "log": log_messages[-25:],
    }


HTML_CONTENT = """<!DOCTYPE html>
<html lang="hu">
<head>
  <meta charset="UTF-8">
  <title>Pincer Board Game - Human vs Bot</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    body { background: #121820; color: #e6edf3; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
    header { background: #1b222d; padding: 12px 24px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #30363d; }
    .badge { padding: 4px 10px; border-radius: 12px; font-weight: bold; font-size: 13px; text-transform: uppercase; }
    .badge-harvest { background: #d29922; color: #121820; }
    .badge-mobilization { background: #388bfd; color: #fff; }
    .badge-development { background: #238636; color: #fff; }
    .board-pane {
      flex: 1;
      display: flex;
      flex-direction: column;
      position: relative;
      background: radial-gradient(circle, #1a2332 0%, #0d1117 100%);
      padding: 12px 16px;
      overflow: hidden;
    }
    .svg-wrapper {
      flex: 1;
      width: 100%;
      height: 100%;
      min-height: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      overflow: hidden;
    }
    svg {
      width: 100%;
      height: 100%;
      max-width: 100%;
      max-height: 100%;
    }
    .hex-tile { cursor: pointer; transition: 0.2s; stroke-width: 2.5; stroke-linejoin: round; }
    .hex-tile:hover { filter: brightness(1.18); stroke-width: 3.5; }
    .node-highlight-move { stroke: #f0883e !important; stroke-width: 5 !important; filter: drop-shadow(0 0 8px rgba(240, 136, 62, 0.8)); }
    .node-highlight-attack { stroke: #f85149 !important; stroke-width: 5 !important; filter: drop-shadow(0 0 10px rgba(248, 81, 73, 0.9)); }
    .edge-line { stroke: #30363d; stroke-width: 4; stroke-linecap: round; }
    .edge-road-p1 { stroke: #58a6ff !important; stroke-width: 7 !important; stroke-linecap: round; }
    .edge-road-p2 { stroke: #f85149 !important; stroke-width: 7 !important; stroke-linecap: round; }
    .edge-water-bridge { stroke: #d29922 !important; stroke-width: 6 !important; stroke-dasharray: 4, 3; }
    .winner-banner { position: absolute; top: 20px; background: rgba(35, 134, 54, 0.95); color: white; padding: 14px 28px; border-radius: 8px; font-size: 18px; font-weight: bold; border: 2px solid #3fb950; z-index: 10; box-shadow: 0 10px 30px rgba(0,0,0,0.8); }
    .action-bar {
      margin-top: 8px;
      display: flex;
      justify-content: center;
      gap: 10px;
      background: #1b222d;
      padding: 10px 18px;
      border-radius: 8px;
      border: 1px solid #30363d;
      box-shadow: 0 4px 14px rgba(0,0,0,0.4);
      z-index: 5;
    }
    .board-dropdown {
      background: #21262d;
      color: #58a6ff;
      border: 1px solid #388bfd;
      padding: 5px 12px;
      border-radius: 6px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      outline: none;
      transition: background 0.2s;
    }
    .board-dropdown:hover {
      background: #30363d;
    }
  </style>
</head>
<body>
  <header>
    <div style="display: flex; align-items: center; gap: 14px;">
      <h1 style="font-size: 18px; margin: 0;">Pincer AI — Játék a Bot ellen</h1>
      <select id="boardSelect" class="board-dropdown" onchange="onBoardSelect(this.value)">
        <option value="full_58" selected>Teljes Tábla (58 mező - Classic)</option>
        <option value="synthetic">Teszttábla (10 mező - Szintetikus)</option>
      </select>
      <span id="turnIndicator" style="color: #8b949e; font-size: 14px;">Kör: 1</span>
    </div>
    <div style="display: flex; gap: 10px; align-items: center;">
      <span id="phaseBadge" class="badge badge-harvest">Harvest</span>
      <button class="btn btn-secondary" onclick="resetGame()">Új Játék</button>
    </div>
  </header>

  <div class="main-container">
    <div class="board-pane">
      <div id="winnerBanner" class="winner-banner" style="display: none;"></div>
      <div class="svg-wrapper">
        <svg id="boardSvg" viewBox="15 5 580 680" preserveAspectRatio="xMidYMid meet"></svg>
      </div>
      <div class="action-bar" id="actionBar"></div>
    </div>

    <div class="side-pane">
      <div class="card">
        <h3>Te készleteid (Kék - P1)</h3>
        <div class="res-grid" id="p1Res"></div>
        <div style="margin-top: 10px; font-size: 12px; color: #8b949e;">
          Kolóniák: <b id="p1Colonies" style="color:#58a6ff">1</b> | Cserearány: <b id="p1Rate" style="color:#58a6ff">5:1</b>
        </div>
      </div>

      <div class="card">
        <h3>Bot készletei (Piros - P2)</h3>
        <div class="res-grid" id="p2Res"></div>
        <div style="margin-top: 10px; font-size: 12px; color: #8b949e;">
          Kolóniák: <b id="p2Colonies" style="color:#f85149">1</b> | Cserearány: <b id="p2Rate" style="color:#f85149">5:1</b>
        </div>
      </div>

      <div class="card" style="flex: 1; display: flex; flex-direction: column;">
        <h3>Eseménynapló</h3>
        <div class="log-container" id="logBox"></div>
      </div>
    </div>
  </div>

  <script>
    let state = null;
    let selectedUnitId = null;

    const TERRAIN_COLORS = {
      land: "#2ea043",
      woods: "#196c2e",
      wheat: "#d29922",
      stone: "#6e7681",
      hills: "#8d5338",
      mountain: "#484f58",
      water: "#1f6feb"
    };

    async function fetchState() {
      const res = await fetch("/api/state");
      state = await res.json();
      render();
    }

    function render() {
      if (document.getElementById("boardSelect") && state.board_type) {
        document.getElementById("boardSelect").value = state.board_type;
      }
      document.getElementById("turnIndicator").innerText = `Kör: ${state.turn} | Aktív játékos: ${state.current_player}`;
      const badge = document.getElementById("phaseBadge");
      badge.innerText = state.phase;
      badge.className = `badge badge-${state.phase}`;

      if (state.winner) {
        const w = document.getElementById("winnerBanner");
        w.innerText = `GYŐZELEM! A(z) ${state.winner} játékos nyert!`;
        w.style.display = "block";
      } else {
        document.getElementById("winnerBanner").style.display = "none";
      }

      renderResources("p1Res", state.p1.resources);
      renderResources("p2Res", state.p2.resources);
      document.getElementById("p1Colonies").innerText = state.p1.colonies_count;
      document.getElementById("p2Colonies").innerText = state.p2.colonies_count;
      document.getElementById("p1Rate").innerText = `${state.p1.exchange_rate}:1`;
      document.getElementById("p2Rate").innerText = `${state.p2.exchange_rate}:1`;

      const logBox = document.getElementById("logBox");
      logBox.innerHTML = state.log.map(m => `<div class="log-item">${m}</div>`).join("");
      logBox.scrollTop = logBox.scrollHeight;

      renderBoard();
      renderActionBar();
    }

    function renderResources(elId, res) {
      const el = document.getElementById(elId);
      const items = ["wood", "wheat", "stone", "iron_ore", "gold", "sheep"];
      el.innerHTML = items.map(k => `
        <div class="res-item">
          <div class="res-name">${k}</div>
          <div class="res-val">${res[k] || 0}</div>
        </div>
      `).join("");
    }

    function getHexPoints(cx, cy, r) {
      const points = [];
      for (let i = 0; i < 6; i++) {
        const rad = (Math.PI / 180) * (60 * i);
        const x = cx + r * Math.cos(rad);
        const y = cy + r * Math.sin(rad);
        points.push(`${x.toFixed(1)},${y.toFixed(1)}`);
      }
      return points.join(" ");
    }

    function renderBoard() {
      const svg = document.getElementById("boardSvg");
      if (state.view_box) {
        svg.setAttribute("viewBox", state.view_box);
      }
      let html = "";

      // Render edges (roads, bridges, borders)
      for (const e of state.edges) {
        let cls = "edge-line";
        if (e.road_owner === "P1") cls += " edge-road-p1";
        else if (e.road_owner === "P2") cls += " edge-road-p2";
        else if (e.bridge_owner) cls += " edge-water-bridge";
        html += `<line x1="${e.x1}" y1="${e.y1}" x2="${e.x2}" y2="${e.y2}" class="${cls}" />`;
      }

      // Legal moves for selected unit
      const legalTargets = new Set();
      const attackTargets = new Set();
      if (selectedUnitId) {
        for (const act of state.legal_actions) {
          if (act.type === "MoveUnitAction" && act.unit_id === selectedUnitId) {
            legalTargets.add(act.target_node_id);
          }
          if (act.type === "AttackAction" && act.attacker_unit_id === selectedUnitId) {
            attackTargets.add(act.target_node_id);
          }
          if (act.type === "CounterMoveAction" && act.defender_unit_id === selectedUnitId) {
            if (act.is_attack) attackTargets.add(act.target_node_id);
            else legalTargets.add(act.target_node_id);
          }
        }
      }

      const is58 = state.is_58;
      const hexRadius = state.hex_radius || (is58 ? 38 : 66);

      for (const n of state.nodes) {
        const bg = TERRAIN_COLORS[n.terrain] || "#30363d";
        let stroke = "#1c2128";
        let extraCls = "";

        if (legalTargets.has(n.id)) { extraCls = "node-highlight-move"; stroke = "#f0883e"; }
        if (attackTargets.has(n.id)) { extraCls = "node-highlight-attack"; stroke = "#f85149"; }

        const points = getHexPoints(n.x, n.y, hexRadius);

        html += `
          <g onclick="onNodeClick('${n.id}')" style="cursor: pointer;">
            <!-- Hexagon Polygon -->
            <polygon points="${points}" fill="${bg}" stroke="${stroke}" class="hex-tile ${extraCls}" />
        `;

        if (is58) {
          // Compact sizing for 58-tile board
          if (n.harvest_value) {
            html += `
              <circle cx="${n.x}" cy="${n.y - 15}" r="9" fill="#f0e6d2" stroke="#3c342b" stroke-width="1.2" />
              <text x="${n.x}" y="${n.y - 11.5}" fill="#24292f" font-size="10" font-weight="900" text-anchor="middle">${n.harvest_value}</text>
            `;
          } else if (n.terrain === "mountain") {
            html += `<text x="${n.x}" y="${n.y - 14}" font-size="12" text-anchor="middle">⛰️</text>`;
          } else if (n.terrain === "water") {
            html += `<text x="${n.x}" y="${n.y - 14}" font-size="10" text-anchor="middle">🌊</text>`;
          }

          html += `
            <text x="${n.x}" y="${n.y + 23}" fill="#ffffff" font-size="9" font-weight="bold" text-anchor="middle">${n.id}</text>
            <text x="${n.x}" y="${n.y + 31.5}" fill="rgba(255,255,255,0.7)" font-size="7" text-anchor="middle">${n.terrain}</text>
          `;

          if (n.colony) {
            const colColor = n.colony.controller === "P1" ? "#1f6feb" : "#da3633";
            const fortLabel = n.colony.has_fort ? "🏰 FORT" : "🏛️ COL";
            html += `
              <rect x="${n.x - 20}" y="${n.y + 7}" width="40" height="11" rx="2" fill="${colColor}" stroke="#fff" stroke-width="0.8" />
              <text x="${n.x}" y="${n.y + 15}" fill="#fff" font-size="6.5" font-weight="bold" text-anchor="middle">${fortLabel}</text>
            `;
          } else if (n.port) {
            html += `
              <rect x="${n.x - 17}" y="${n.y + 7}" width="34" height="11" rx="2" fill="#0969da" stroke="#58a6ff" stroke-width="0.8" />
              <text x="${n.x}" y="${n.y + 15}" fill="#fff" font-size="6.5" font-weight="bold" text-anchor="middle">⚓ PORT</text>
            `;
          }

          if (n.unit) {
            const uColor = n.unit.owner === "P1" ? "#388bfd" : "#f85149";
            const isSelected = (n.unit.id === selectedUnitId);
            const uStroke = isSelected ? "#f0883e" : "#ffffff";
            const uStrokeWidth = isSelected ? "2.5" : "1.2";
            const unitLabels = { musketeer: "M", cavalry: "C", cannon: "Cn", frigate: "F" };
            const uLetter = unitLabels[n.unit.type] || n.unit.type[0].toUpperCase();

            html += `
              <circle cx="${n.x}" cy="${n.y - 1}" r="11" fill="${uColor}" stroke="${uStroke}" stroke-width="${uStrokeWidth}" filter="drop-shadow(0 2px 4px rgba(0,0,0,0.7))" />
              <text x="${n.x}" y="${n.y + 2.5}" fill="#fff" font-size="9" font-weight="900" text-anchor="middle">${uLetter}</text>
            `;
          }
        } else {
          // Large sizing for 10-tile synthetic board
          if (n.harvest_value) {
            html += `
              <circle cx="${n.x}" cy="${n.y - 25}" r="14" fill="#f0e6d2" stroke="#3c342b" stroke-width="1.5" />
              <text x="${n.x}" y="${n.y - 20}" fill="#24292f" font-size="13" font-weight="900" text-anchor="middle">${n.harvest_value}</text>
            `;
          } else if (n.terrain === "mountain") {
            html += `<text x="${n.x}" y="${n.y - 22}" font-size="17" text-anchor="middle">⛰️</text>`;
          } else if (n.terrain === "water") {
            html += `<text x="${n.x}" y="${n.y - 22}" font-size="14" text-anchor="middle">🌊</text>`;
          }

          html += `
            <text x="${n.x}" y="${n.y + 36}" fill="#ffffff" font-size="11" font-weight="bold" text-anchor="middle">${n.id}</text>
            <text x="${n.x}" y="${n.y + 48}" fill="rgba(255,255,255,0.7)" font-size="9" text-anchor="middle">${n.terrain}</text>
          `;

          if (n.colony) {
            const colColor = n.colony.controller === "P1" ? "#1f6feb" : "#da3633";
            const fortLabel = n.colony.has_fort ? "🏰 WALL" : "🏛️ COLONY";
            html += `
              <rect x="${n.x - 30}" y="${n.y + 14}" width="60" height="15" rx="3" fill="${colColor}" stroke="#fff" stroke-width="1" />
              <text x="${n.x}" y="${n.y + 25}" fill="#fff" font-size="8.5" font-weight="bold" text-anchor="middle">${fortLabel}</text>
            `;
          } else if (n.port) {
            html += `
              <rect x="${n.x - 24}" y="${n.y + 14}" width="48" height="15" rx="3" fill="#0969da" stroke="#58a6ff" stroke-width="1" />
              <text x="${n.x}" y="${n.y + 25}" fill="#fff" font-size="9" font-weight="bold" text-anchor="middle">⚓ PORT</text>
            `;
          }

          if (n.unit) {
            const uColor = n.unit.owner === "P1" ? "#388bfd" : "#f85149";
            const isSelected = (n.unit.id === selectedUnitId);
            const uStroke = isSelected ? "#f0883e" : "#ffffff";
            const uStrokeWidth = isSelected ? "3.5" : "1.5";
            const unitLabels = { musketeer: "M", cavalry: "C", cannon: "Cn", frigate: "F" };
            const uLetter = unitLabels[n.unit.type] || n.unit.type[0].toUpperCase();

            html += `
              <circle cx="${n.x}" cy="${n.y}" r="17" fill="${uColor}" stroke="${uStroke}" stroke-width="${uStrokeWidth}" filter="drop-shadow(0 2px 5px rgba(0,0,0,0.7))" />
              <text x="${n.x}" y="${n.y + 5}" fill="#fff" font-size="12" font-weight="900" text-anchor="middle">${uLetter}</text>
            `;
          }
        }

        html += `</g>`;
      }

      svg.innerHTML = html;
    }

    function renderActionBar() {
      const bar = document.getElementById("actionBar");
      if (state.winner) {
        bar.innerHTML = `<button class="btn btn-secondary" onclick="resetGame()">Új Játék Indítása</button>`;
        return;
      }

      if (state.counter_move_active && state.counter_move_defender === "P1") {
        bar.innerHTML = `
          <span style="align-self: center; font-weight: bold; color: #f85149;">Ellenlépési Reakció!</span>
          <button class="btn btn-secondary" onclick="executeAction({type: 'PassCounterMoveAction', player: 'P1'})">Ellenlépés Passzolása</button>
        `;
        return;
      }

      if (state.current_player !== "P1") {
        bar.innerHTML = `<span style="align-self: center; color: #8b949e;">A Bot (P2) gondolkodik...</span>`;
        return;
      }

      let html = "";
      if (state.phase === "harvest") {
        html += `<button class="btn" onclick="executeAction({type: 'HarvestRollAction', player: 'P1'})">🎲 Kockadobás (Harvest)</button>`;
      } else if (state.phase === "mobilization") {
        html += `<span style="align-self: center; font-size: 13px; color: #8b949e;">Kattints egy Kék egységedre a lépéshez/támadáshoz.</span>`;
        html += `<button class="btn btn-secondary" onclick="executeAction({type: 'EndPhaseAction', player: 'P1'})">Mobilization Befejezése ➔</button>`;
      } else if (state.phase === "development") {
        const canBuildColony = state.legal_actions.some(a => a.type === "BuildColonyAction");
        const canBuildPort = state.legal_actions.some(a => a.type === "BuildPortAction");
        const canBuildFort = state.legal_actions.some(a => a.type === "BuildFortAction");
        const canRecruitMusketeer = state.legal_actions.some(a => a.type === "RecruitUnitAction" && a.unit_type === "musketeer");

        if (canBuildColony) {
          const act = state.legal_actions.find(a => a.type === "BuildColonyAction");
          html += `<button class="btn" onclick='executeAction(${JSON.stringify(act)})'>Kolónia Építése</button>`;
        }
        if (canBuildPort) {
          const act = state.legal_actions.find(a => a.type === "BuildPortAction");
          html += `<button class="btn" onclick='executeAction(${JSON.stringify(act)})'>Kikötő Építése</button>`;
        }
        if (canBuildFort) {
          const act = state.legal_actions.find(a => a.type === "BuildFortAction");
          html += `<button class="btn" onclick='executeAction(${JSON.stringify(act)})'>Fal Építése</button>`;
        }
        if (canRecruitMusketeer) {
          const act = state.legal_actions.find(a => a.type === "RecruitUnitAction" && a.unit_type === "musketeer");
          html += `<button class="btn" onclick='executeAction(${JSON.stringify(act)})'>Muskétás Toborzása</button>`;
        }

        html += `<button class="btn btn-secondary" onclick="executeAction({type: 'EndPhaseAction', player: 'P1'})">Kör Befejezése ➔</button>`;
      }

      bar.innerHTML = html;
    }

    function onNodeClick(nodeId) {
      if (state.current_player !== "P1" && !state.counter_move_active) return;

      const node = state.nodes.find(n => n.id === nodeId);
      if (!node) return;

      // If unit is clicked, select it
      if (node.unit && node.unit.owner === "P1") {
        selectedUnitId = node.unit.id;
        renderBoard();
        return;
      }

      // If already selected, check if clicked node is a move or attack target
      if (selectedUnitId) {
        const moveAct = state.legal_actions.find(a => a.type === "MoveUnitAction" && a.unit_id === selectedUnitId && a.target_node_id === nodeId);
        if (moveAct) {
          executeAction(moveAct);
          selectedUnitId = null;
          return;
        }

        const atkAct = state.legal_actions.find(a => a.type === "AttackAction" && a.attacker_unit_id === selectedUnitId && a.target_node_id === nodeId);
        if (atkAct) {
          executeAction(atkAct);
          selectedUnitId = null;
          return;
        }

        // Counter-move attack / move
        const counterAct = state.legal_actions.find(a => a.type === "CounterMoveAction" && a.defender_unit_id === selectedUnitId && a.target_node_id === nodeId);
        if (counterAct) {
          executeAction(counterAct);
          selectedUnitId = null;
          return;
        }

        selectedUnitId = null;
        renderBoard();
      }
    }

    async function executeAction(action) {
      const res = await fetch("/api/action", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(action)
      });
      state = await res.json();
      selectedUnitId = null;
      render();
    }

    async function onBoardSelect(newType) {
      const res = await fetch("/api/reset", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ board_type: newType })
      });
      state = await res.json();
      selectedUnitId = null;
      render();
    }

    async function resetGame() {
      const bSelect = document.getElementById("boardSelect");
      const currentBoard = bSelect ? bSelect.value : (state ? state.board_type : "full_58");
      await onBoardSelect(currentBoard);
    }

    fetchState();
  </script>
</body>
</html>
"""


class PincerRequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/" or parsed.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_CONTENT.encode("utf-8"))
        elif parsed.path == "/api/state":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            data = serialize_state(session.state, session.log, board_type=session.board_type)
            self.wfile.write(json.dumps(data).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)

        if parsed.path == "/api/reset":
            payload = json.loads(post_data.decode("utf-8")) if post_data else {}
            b_type = payload.get("board_type", session.board_type)
            session.reset(board_type=b_type)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            data = serialize_state(session.state, session.log, board_type=session.board_type)
            self.wfile.write(json.dumps(data).encode("utf-8"))
            return

        if parsed.path == "/api/action":
            payload = json.loads(post_data.decode("utf-8")) if post_data else {}
            act_type = payload.get("type")
            p_id = PlayerId(payload.get("player", "P1"))

            action = None
            if act_type == "HarvestRollAction":
                action = HarvestRollAction(player_id=p_id)
            elif act_type == "MoveUnitAction":
                action = MoveUnitAction(player_id=p_id, unit_id=payload["unit_id"], target_node_id=payload["target_node_id"])
            elif act_type == "AttackAction":
                action = AttackAction(player_id=p_id, attacker_unit_id=payload["attacker_unit_id"], target_node_id=payload["target_node_id"])
            elif act_type == "CounterMoveAction":
                action = CounterMoveAction(player_id=p_id, defender_unit_id=payload["defender_unit_id"], target_node_id=payload["target_node_id"])
            elif act_type == "PassCounterMoveAction":
                action = PassCounterMoveAction(player_id=p_id)
            elif act_type == "BuildColonyAction":
                action = BuildColonyAction(player_id=p_id, node_id=payload["node_id"])
            elif act_type == "BuildPortAction":
                action = BuildPortAction(player_id=p_id, node_id=payload["node_id"], adjacent_colony_id=payload["adjacent_colony_id"])
            elif act_type == "BuildFortAction":
                action = BuildFortAction(player_id=p_id, colony_id=payload["colony_id"])
            elif act_type == "BuildRoadAction":
                action = BuildRoadAction(player_id=p_id, edge_id=payload["edge_id"])
            elif act_type == "RecruitUnitAction":
                action = RecruitUnitAction(player_id=p_id, unit_type=UnitType(payload["unit_type"]), target_node_id=payload["target_node_id"])
            elif act_type == "EndPhaseAction":
                action = EndPhaseAction(player_id=p_id)

            if action:
                try:
                    desc = session._describe_action(action)
                    PincerEngine.apply_action(session.state, action)
                    session.log.append(f"[P1] {desc}")
                    # Let bot act if it is now bot's turn
                    session.run_bot_turns_if_needed()
                except Exception as e:
                    session.log.append(f"[HIBA] {str(e)}")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            data = serialize_state(session.state, session.log, board_type=session.board_type)
            self.wfile.write(json.dumps(data).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        # Quiet console logging
        pass


def main():
    parser = argparse.ArgumentParser(description="Start interactive Pincer Web UI.")
    parser.add_argument("--port", type=int, default=8000, help="HTTP server port.")
    parser.add_argument("--no-browser", action="store_true", help="Do not automatically open browser.")
    args = parser.parse_args()

    server_address = ("127.0.0.1", args.port)
    httpd = http.server.HTTPServer(server_address, PincerRequestHandler)
    url = f"http://localhost:{args.port}"

    print("=" * 60)
    print(f" Pincer Web UI fut a következő címen: {url}")
    print(" Nyisd meg a böngészőben a játékhoz!")
    print(" Leállítás: Ctrl+C a terminálban.")
    print("=" * 60)

    if not args.no_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nSzerver leállítva.")


if __name__ == "__main__":
    main()
