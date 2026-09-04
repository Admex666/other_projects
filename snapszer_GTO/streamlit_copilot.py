"""
Streamlit Live GTO Co-Pilot Dashboard for Schnapsen
Interactive Assistant: Reads cards from Android emulator, tracks points & unseen deck,
and lets you record opponent response moves and reset games with a single click.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import cv2
import numpy as np
import streamlit as st
from adbutils import adb

from src.android_vision import AndroidCardDetector, card_to_hungarian, suit_to_hungarian
from src.game_tracker import (
    SchnapsenTracker,
    ALL_20_CARDS,
    SUIT_HU,
    RANK_HU,
    to_hu,
    get_card_value,
    determine_trick_winner,
)
from src.bot import GTOExploitBot

st.set_page_config(
    page_title="Schnapsen GTO Co-Pilot",
    page_icon="🃏",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for modern styling
st.markdown("""
<style>
    .main { background-color: #0f172a; color: #f8fafc; }
    .stMetric { background: #1e293b; padding: 12px; border-radius: 10px; border: 1px solid #334155; }
    .card-badge {
        display: inline-block;
        padding: 6px 12px;
        margin: 4px;
        border-radius: 8px;
        font-weight: bold;
        font-size: 14px;
    }
    .badge-hearts { background: #7f1d1d; color: #fecaca; border: 1px solid #dc2626; }
    .badge-diamonds { background: #78350f; color: #fef08a; border: 1px solid #eab308; }
    .badge-spades { background: #14532d; color: #bbf7d0; border: 1px solid #22c55e; }
    .badge-clubs { background: #451a03; color: #fed7aa; border: 1px solid #f97316; }
</style>
""", unsafe_allow_html=True)


# Initialize Session State
if "tracker" not in st.session_state:
    st.session_state.tracker = SchnapsenTracker()
if "detector" not in st.session_state:
    st.session_state.detector = AndroidCardDetector()
if "last_screen" not in st.session_state:
    st.session_state.last_screen = None
if "last_action" not in st.session_state:
    st.session_state.last_action = "Nincs rögzített lépés."

tracker: SchnapsenTracker = st.session_state.tracker
detector: AndroidCardDetector = st.session_state.detector


# Helper functions
def get_adb_device():
    try:
        devices = adb.device_list()
        return devices[0] if devices else None
    except Exception:
        return None


def sync_from_emulator():
    device = get_adb_device()
    if not device:
        st.toast("Nincs ADB eszköz csatlakoztatva!", icon="⚠️")
        return

    pil_img = device.screenshot()
    screen_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    st.session_state.last_screen = screen_bgr

    # 1. Adu felderítése
    if not tracker.trump_card:
        t_card, t_hu, t_conf = detector.detect_trump_card(screen_bgr, save_debug=False)
        if t_card and t_conf > 0.40:
            tracker.set_trump(t_card)

    # 2. Saját lapok felderítése
    hand_res = detector.detect_hand_cards(screen_bgr)
    current_hand = [r["card_name"] for r in hand_res if not r["empty"] and r["card_name"]]
    tracker.update_my_hand(current_hand)

    # 3. Ellenfél hívása az asztalon
    opp_code, opp_hu, opp_conf = detector.detect_opponent_card(screen_bgr)
    st.session_state.opp_lead_card = opp_code
    st.toast("Képernyő sikeresen szinkronizálva!", icon="✔")


# ==========================================
# SIDEBAR: Vezérlők & Állapot
# ==========================================
with st.sidebar:
    st.title("🃏 GTO Co-Pilot")
    st.caption("Schnapsen Android Élő Asszisztens")

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        if st.button("🔄 Képernyő Sync", use_container_width=True, type="primary"):
            sync_from_emulator()
    with col_s2:
        if st.button("🗑️ Új parti (Reset)", use_container_width=True):
            tracker.reset_match()
            st.session_state.opp_lead_card = None
            st.session_state.last_action = "Új parti indítva, minden törölve."
            st.rerun()

    st.divider()

    # Manuális Adu beállítás / felülbírálás ha szükséges
    st.subheader("Adu Beállítás")
    current_trump = tracker.trump_card or "Nincs kiválasztva"
    st.write(f"Aktuális: **{to_hu(tracker.trump_card)}** ({tracker.trump_suit or '-'})")

    manual_trump = st.selectbox(
        "Adu kártya beállítása kézzel:",
        ["-"] + ALL_20_CARDS,
        format_func=lambda x: to_hu(x) if x != "-" else "Válassz...",
    )
    if manual_trump != "-" and manual_trump != tracker.trump_card:
        tracker.set_trump(manual_trump)
        st.rerun()

    talon_state = st.checkbox("Zárt talon (2. fázis)", value=tracker.talon_closed)
    tracker.talon_closed = talon_state

    st.divider()
    st.caption(f"Legutóbbi esemény: {st.session_state.last_action}")


# ==========================================
# FŐ NÉZET: Scoreboard & Élő Dashboard
# ==========================================
c_score1, c_score2, c_score3 = st.columns([2, 2, 3])

with c_score1:
    st.metric(
        label="🟢 Saját pontjaid",
        value=f"{tracker.my_score} / 66",
        delta=f"{tracker.my_tricks_count} ütés",
    )
    st.progress(min(1.0, tracker.my_score / 66.0))

with c_score2:
    st.metric(
        label="🔴 Ellenfél pontjai",
        value=f"{tracker.opp_score} / 66",
        delta=f"{tracker.opp_tricks_count} ütés",
    )
    st.progress(min(1.0, tracker.opp_score / 66.0))

with c_score3:
    st.subheader("Adu és Játékfázis")
    if tracker.trump_suit:
        badge_cls = f"badge-{tracker.trump_suit.lower()}"
        st.markdown(
            f'<span class="card-badge {badge_cls}">Adu: {SUIT_HU[tracker.trump_suit]} ({to_hu(tracker.trump_card)})</span>'
            f'<span> | {"🔒 Zárt talon" if tracker.talon_closed else "📖 Nyitott talon"}</span>',
            unsafe_allow_html=True,
        )
    else:
        st.info("Kattints a 'Képernyő Sync' gombra az adu beolvasásához!")


st.divider()

# ==========================================
# 1. KÉZBEN LÉVŐ LAPJAID ÉS SAJÁT LÉPÉS
# ==========================================
col_hand, col_opp_action = st.columns([1, 1])

with col_hand:
    st.subheader("🖐️ Saját lapjaid a kézben")
    if tracker.my_current_hand:
        for idx, card in enumerate(tracker.my_current_hand, 1):
            val = get_card_value(card)
            suit = card.split("_")[0]
            badge_cls = f"badge-{suit.lower()}"
            st.markdown(
                f'<span class="card-badge {badge_cls}">{idx}. {to_hu(card)} ({val} pont)</span>',
                unsafe_allow_html=True,
            )
    else:
        st.write("Nincsenek lapok beolvasva. Nyomj a 'Képernyő Sync'-re.")

# ==========================================
# 2. ELLENFÉL ÜTÉSÉNEK KÉZI BEKATTINTÁSA
# ==========================================
with col_opp_action:
    st.subheader("⚡ Ellenfél válasza / ütése")
    st.write("Amikor **te hívtál**, és az ellenfél elütötte vagy válaszolt rá, **itt kattints rá, mivel felelt!**")

    # Válaszd ki, hogy te mit hívtál
    my_lead_card = st.selectbox(
        "Te mit hívtál ki?",
        ["-"] + (tracker.my_current_hand or ALL_20_CARDS),
        format_func=lambda x: to_hu(x) if x != "-" else "Válassz...",
        key="my_lead_select",
    )

    st.write("**Mivel felelt / ütött az ellenfél?**")
    unseen_cards = tracker.get_unseen_cards()

    # Gombok csoportosítva színek szerint a gyors kattintáshoz
    for suit in ["HEARTS", "DIAMONDS", "SPADES", "CLUBS"]:
        suit_cards = [c for c in unseen_cards if c.startswith(suit)]
        if suit_cards:
            cols = st.columns(len(suit_cards))
            for i, card in enumerate(suit_cards):
                pts = get_card_value(card)
                btn_label = f"{RANK_HU[card.split('_')[1]]} ({pts}p)"
                if cols[i].button(btn_label, key=f"opp_play_{card}", use_container_width=True):
                    if my_lead_card != "-":
                        tracker.record_trick(leader="ME", leader_card=my_lead_card, follower_card=card)
                        st.session_state.last_action = f"Te: {to_hu(my_lead_card)} vs Ellenfél: {to_hu(card)}"
                        # Frissítsük a kezet: vegyük ki a kijátszott lapot
                        if my_lead_card in tracker.my_current_hand:
                            tracker.my_current_hand.remove(my_lead_card)
                        st.toast(f"Leütve! Ellenfél: {to_hu(card)}", icon="✅")
                        st.rerun()
                    else:
                        st.error("Kérlek válaszd ki fent, hogy te mit hívtál ki!")


st.divider()

# ==========================================
# 3. ISMERETLEN LAPOK (TALON + ELLENFÉL KÉZ)
# ==========================================
st.subheader(f"🔍 Ismeretlen lapok ({len(unseen_cards)} db van még játékban)")
st.caption("Ezek a lapok vannak még a talonban vagy az ellenfél kezében:")

c1, c2, c3, c4 = st.columns(4)
col_map = {"HEARTS": c1, "DIAMONDS": c2, "SPADES": c3, "CLUBS": c4}

for suit, col in col_map.items():
    with col:
        st.write(f"**{SUIT_HU[suit]}**")
        cards = [c for c in unseen_cards if c.startswith(suit)]
        if not cards:
            st.caption("Mind ismert / kijátszva")
        for card in cards:
            val = get_card_value(card)
            badge_cls = f"badge-{suit.lower()}"
            st.markdown(f'<span class="card-badge {badge_cls}">{to_hu(card)} ({val}p)</span>', unsafe_allow_html=True)

# Ütéstörténet táblázat
if tracker.trick_history:
    st.divider()
    st.subheader("📜 Ütéstörténet")
    history_data = []
    for idx, t in enumerate(tracker.trick_history, 1):
        winner_str = "🟢 Te vitted" if t["winner"] == "ME" else "🔴 Ellenfél vitte"
        leader_str = "Te hívtál" if t["leader"] == "ME" else "Ellenfél hívott"
        history_data.append({
            "Ütés": f"#{idx}",
            "Kezdő": leader_str,
            "Hívott lap": to_hu(t["leader_card"]),
            "Válasz lap": to_hu(t["follower_card"]),
            "Győztes": winner_str,
            "Pontok": f"+{t['points']} pont",
        })
    st.table(history_data)
