"""
Last-Minute Wellness Marketplace - Scenario Simulator
======================================================
Futtatás: python wellness_marketplace_sim.py
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from dataclasses import dataclass, field
from typing import List

# ─────────────────────────────────────────────
# ADATSTRUKTÚRA
# ─────────────────────────────────────────────

@dataclass
class Scenario:
    name: str

    # --- DEMAND / MARKETING ---
    # Forrás: Meta/Facebook HU szépségipar CPM: 1500-3000 Ft (ppconline.hu)
    #          TikTok HU CPM: ~171 Ft, CPC: ~91 Ft (selector.hu, 2024)
    #          1 Ft/megjelenés = CPM 1000 Ft
    #
    #  Logika: ad_spend = impressions × cpm / 1000
    #          clicks   = impressions × ctr
    #          cpc      = ad_spend / clicks  (DERIVED)
    #          cac      = ad_spend / new_bookings  (DERIVED)
    impressions: float = 1_000_000        # megjelenések száma
    cpm: float = 1_000                    # cost per 1000 impressions (Ft) — ez az igazi input
    ctr: float = 0.015                    # click-through rate (pl. 0.015 = 1.5%)
    cvr: float = 0.04                     # booking conversion rate (pl. 0.04 = 4%)

    # --- PRODUCT ---
    aov: float = 15_000                   # átlagos rendelési érték (Ft)
    take_rate: float = 0.12               # marketplace jutalék (pl. 0.12 = 12%)
    variable_cost_rate: float = 0.04      # payment + support + refund (% of revenue)

    # --- RETENTION ---
    bookings_per_user_per_month: float = 1.5   # havi booking frekvencia
    monthly_churn: float = 0.20                # havi churn rate

    # --- SUPPLY ---
    partners: int = 50                    # aktív partnerek száma
    idle_slots_per_partner_per_day: float = 2.0  # napi üres slot/partner
    discount_depth: float = 0.30          # diszkont mélysége (pl. 0.30 = 30%)
    fill_rate: float = 0.30               # feltöltött slotok hány %-a kel el

    # --- FIXED COSTS (Ft/hó) ---
    payroll: float = 3_000_000            # bérek
    marketing_fixed: float = 2_000_000   # hirdetési büdzsé
    infra: float = 300_000               # szerver, tool
    support_fixed: float = 500_000       # support csapat

    # --- OPERATING DAYS ---
    days_per_month: int = 26


# ─────────────────────────────────────────────
# SZÁMÍTÁS
# ─────────────────────────────────────────────

def simulate(s: Scenario) -> dict:
    r = {}

    # --- DEMAND FUNNEL ---
    # Az igazi input: CPM (mennyit fizetünk 1000 megjelenésért)
    ad_spend = s.impressions * s.cpm / 1000      # hirdetési költség
    clicks = s.impressions * s.ctr               # kattintások
    new_bookings = clicks * s.cvr                # új bookingok a kampanyból
    cpc = ad_spend / clicks if clicks > 0 else float("inf")   # derived
    cac = ad_spend / new_bookings if new_bookings > 0 else float("inf")  # derived

    r["clicks"] = clicks
    r["ad_spend"] = ad_spend
    r["new_bookings_from_campaign"] = new_bookings
    r["cpc"] = cpc
    r["cac"] = cac
    r["cpm"] = s.cpm
    r["cost_per_impression"] = s.cpm / 1000      # Ft / megjelenés

    # --- SUPPLY INVENTORY ---
    total_slots_per_month = s.partners * s.idle_slots_per_partner_per_day * s.days_per_month
    booked_slots = total_slots_per_month * s.fill_rate
    discounted_price = s.aov * (1 - s.discount_depth)

    r["total_idle_slots_per_month"] = total_slots_per_month
    r["booked_slots_per_month"] = booked_slots
    r["discounted_price"] = discounted_price

    # --- GMV & REVENUE ---
    gmv = booked_slots * discounted_price
    revenue = gmv * s.take_rate

    # Változó költségek 2 komponense:
    # 1. Ops: payment processing + refund + support (revenue arányos)
    variable_costs_ops = revenue * s.variable_cost_rate
    # 2. Marketing: ad_spend (skálázható, booking-arányos — nem overhead)
    variable_costs_marketing = ad_spend
    total_variable_costs = variable_costs_ops + variable_costs_marketing

    contribution = revenue - total_variable_costs
    contribution_per_booking = contribution / booked_slots if booked_slots > 0 else 0
    marketing_cost_per_booking = variable_costs_marketing / booked_slots if booked_slots > 0 else 0

    r["gmv"] = gmv
    r["revenue"] = revenue
    r["variable_costs_ops"] = variable_costs_ops
    r["variable_costs_marketing"] = variable_costs_marketing
    r["total_variable_costs"] = total_variable_costs
    r["contribution"] = contribution
    r["contribution_per_booking"] = contribution_per_booking
    r["marketing_cost_per_booking"] = marketing_cost_per_booking

    # --- LTV ---
    # LTV-ben a marketing cost per booking is benne van (ez a valódi user-szintű ktg)
    lifetime_months = 1 / s.monthly_churn if s.monthly_churn > 0 else float("inf")
    lifetime_bookings = s.bookings_per_user_per_month * lifetime_months
    revenue_per_booking = s.aov * s.take_rate
    ltv = lifetime_bookings * revenue_per_booking * (1 - s.variable_cost_rate)

    r["lifetime_months"] = lifetime_months
    r["lifetime_bookings"] = lifetime_bookings
    r["revenue_per_booking"] = revenue_per_booking
    r["ltv"] = ltv

    # --- LTV / CAC ---
    ltv_cac = ltv / cac if cac > 0 else float("inf")
    r["ltv_cac"] = ltv_cac

    # --- PARTNER ECONOMICS ---
    incremental_revenue_per_partner = (
        s.idle_slots_per_partner_per_day * s.days_per_month * s.fill_rate * discounted_price
    )
    commission_per_partner = incremental_revenue_per_partner * s.take_rate
    partner_net_gain = incremental_revenue_per_partner - commission_per_partner

    r["incremental_revenue_per_partner"] = incremental_revenue_per_partner
    r["commission_per_partner"] = commission_per_partner
    r["partner_net_gain"] = partner_net_gain

    # --- FIX COSTS & BREAK-EVEN ---
    # Fix = valóban fix: bér + infra + support overhead (marketing NEM fix)
    total_fixed = s.payroll + s.marketing_fixed + s.infra + s.support_fixed
    profit = contribution - total_fixed
    breakeven_bookings = total_fixed / contribution_per_booking if contribution_per_booking > 0 else float("inf")

    r["total_fixed_costs"] = total_fixed
    r["profit"] = profit
    r["breakeven_bookings"] = breakeven_bookings

    # --- LIQUIDITY INDEX (proxy) ---
    # Ha a booked_slots közelít a total_slots-hoz, és sok user van → jó liquidity
    liquidity_score = min(s.fill_rate / 0.40, 1.0) * 100   # 40% fill rate = 100 pont

    r["liquidity_score"] = liquidity_score

    return r


# ─────────────────────────────────────────────
# PRINT
# ─────────────────────────────────────────────

SEP = "─" * 60

def fmt(v, unit="Ft", decimals=0):
    if isinstance(v, float) and v == float("inf"):
        return "∞"
    if unit == "Ft":
        return f"{v:,.0f} Ft"
    if unit == "%":
        return f"{v*100:.1f}%"
    if unit == "x":
        return f"{v:.2f}x"
    if unit == "db":
        return f"{v:,.{decimals}f} db"
    if unit == "hó":
        return f"{v:.1f} hó"
    return f"{v:,.{decimals}f}"

def health(value, good, warn):
    """Emoji jelzés: ✅ jó, ⚠️ közepes, ❌ rossz."""
    if value >= good:
        return "✅"
    if value >= warn:
        return "⚠️ "
    return "❌"

def print_scenario(s: Scenario, r: dict):
    print(f"\n{'═'*60}")
    print(f"  SZCENÁRIÓ: {s.name.upper()}")
    print(f"{'═'*60}")

    print(f"\n{'─'*60}")
    print("  📢 DEMAND FUNNEL (marketing)")
    print(f"{'─'*60}")
    print(f"  Megjelenések:          {fmt(s.impressions, 'db')}")
    print(f"  CPM:                   {fmt(r['cpm'])}  (1000 megjelenés ára — ez az INPUT)")
    print(f"  Költség/megjelenés:    {r['cost_per_impression']:.3f} Ft")
    print(f"  CTR:                   {fmt(s.ctr, '%')}")
    print(f"  Kattintások:           {fmt(r['clicks'], 'db')}")
    print(f"  Hirdetési költség:     {fmt(r['ad_spend'])}  (= impressions × CPM / 1000)")
    print(f"  CPC (derived):         {fmt(r['cpc'])}  (= ad_spend / clicks)")
    print(f"  Booking CVR:           {fmt(s.cvr, '%')}")
    print(f"  Új bookingok:          {fmt(r['new_bookings_from_campaign'], 'db')}")
    print(f"  CAC (derived):         {fmt(r['cac'])}  {health(1/r['cac']*10000, 2, 1)}")

    print(f"\n{'─'*60}")
    print("  🏥 SUPPLY & FOGLALÁSOK")
    print(f"{'─'*60}")
    print(f"  Aktív partnerek:       {s.partners} db")
    print(f"  Üres slot/partner/nap: {s.idle_slots_per_partner_per_day}")
    print(f"  Össz. üres slot/hó:   {fmt(r['total_idle_slots_per_month'], 'db')}")
    print(f"  Fill rate:             {fmt(s.fill_rate, '%')}  {health(s.fill_rate, 0.35, 0.20)}")
    print(f"  Lefoglalt slot/hó:    {fmt(r['booked_slots_per_month'], 'db')}")
    print(f"  Diszkont mélység:      {fmt(s.discount_depth, '%')}")
    print(f"  Eredeti ár (AOV):      {fmt(s.aov)}")
    print(f"  Diszkontált ár:        {fmt(r['discounted_price'])}")

    print(f"\n{'─'*60}")
    print("  💰 GMV / REVENUE")
    print(f"{'─'*60}")
    print(f"  GMV (havi):            {fmt(r['gmv'])}")
    print(f"  Take rate:             {fmt(s.take_rate, '%')}")
    print(f"  Revenue (havi):        {fmt(r['revenue'])}")
    print(f"  Változó ktg — ops:    {fmt(r['variable_costs_ops'])}  ({fmt(s.variable_cost_rate, '%')} of rev — payment/refund/support)")
    print(f"  Változó ktg — mktg:  {fmt(r['variable_costs_marketing'])}  (ad spend, CAC-alapú)")
    print(f"  Össz. változó ktg:    {fmt(r['total_variable_costs'])}")
    print(f"  Contribution margin:   {fmt(r['contribution'])}")
    print(f"  Contribution/booking:  {fmt(r['contribution_per_booking'])}")

    print(f"\n{'─'*60}")
    print("  🔄 RETENTION & LTV")
    print(f"{'─'*60}")
    print(f"  Havi booking/user:     {s.bookings_per_user_per_month}")
    print(f"  Havi churn:            {fmt(s.monthly_churn, '%')}")
    print(f"  Élettartam:            {fmt(r['lifetime_months'], 'hó')}")
    print(f"  Élettartam bookingok:  {fmt(r['lifetime_bookings'], 'db', 1)}")
    print(f"  Revenue/booking:       {fmt(r['revenue_per_booking'])}")
    print(f"  LTV:                   {fmt(r['ltv'])}  {health(r['ltv'], 15000, 8000)}")

    print(f"\n{'─'*60}")
    print("  ⚖️  LTV / CAC")
    print(f"{'─'*60}")
    print(f"  LTV:                   {fmt(r['ltv'])}")
    print(f"  CAC:                   {fmt(r['cac'])}")
    ratio = r["ltv_cac"]
    tag = health(ratio, 3.0, 1.5)
    print(f"  LTV/CAC:               {fmt(ratio, 'x')}  {tag}")
    if ratio < 1:
        print("  ❗ A business jelenlegi paramétereknél veszteséges!")
    elif ratio < 3:
        print("  ⚠️  Elfogadható, de optimalizálás szükséges.")
    else:
        print("  ✅ Egészséges unit economics.")

    print(f"\n{'─'*60}")
    print("  🤝 PARTNER ECONOMICS (átlag/partner/hó)")
    print(f"{'─'*60}")
    print(f"  Inkrementális bevétel:  {fmt(r['incremental_revenue_per_partner'])}")
    print(f"  Jutalék (platform):     {fmt(r['commission_per_partner'])}")
    print(f"  Nettó partner nyereség: {fmt(r['partner_net_gain'])}  {health(r['partner_net_gain'], 300000, 100000)}")

    print(f"\n{'─'*60}")
    print("  🏗️  FIX COSTS & BREAK-EVEN")
    print(f"{'─'*60}")
    print(f"  Bérek:                 {fmt(s.payroll)}")
    print(f"  Infra:                 {fmt(s.infra)}")
    print(f"  Support overhead:      {fmt(s.support_fixed)}")
    if s.marketing_fixed > 0:
        print(f"  Marketing (egyéb fix): {fmt(s.marketing_fixed)}")
    print(f"  Összes fix ktg/hó:    {fmt(r['total_fixed_costs'])}")
    print(f"  [Marketing ad spend a változó költségekben szerepel: {fmt(r['variable_costs_marketing'])}]")
    print(f"  Break-even bookings:   {fmt(r['breakeven_bookings'], 'db')}")
    print(f"  Aktuális bookingok:    {fmt(r['booked_slots_per_month'], 'db')}")
    be_gap = r["booked_slots_per_month"] - r["breakeven_bookings"]
    if be_gap >= 0:
        print(f"  ✅ Break-even felett:  +{fmt(be_gap, 'db')} booking")
    else:
        print(f"  ❌ Break-even alatt:   {fmt(be_gap, 'db')} booking hiány")

    print(f"\n{'─'*60}")
    print("  📊 ÖSSZEFOGLALÓ")
    print(f"{'─'*60}")
    print(f"  Havi profit/veszteség: {fmt(r['profit'])}  {health(r['profit'], 0, -2_000_000)}")
    print(f"  Liquidity score:       {r['liquidity_score']:.0f}/100  {health(r['liquidity_score'], 70, 40)}")
    print(f"{'═'*60}\n")


# ─────────────────────────────────────────────
# RÉSZLETES ELEMZÉS
# ─────────────────────────────────────────────

def analyze_scenario(s: Scenario, r: dict):
    """Részletes, kommentált elemzés minden számhoz."""

    print(f"\n{'#'*60}")
    print(f"  MÉLYELEMZÉS: {s.name}")
    print(f"{'#'*60}")

    # ── 1. DEMAND FUNNEL ──────────────────────────────────────────
    print(f"\n  [1] DEMAND FUNNEL ELEMZÉS")
    print(f"  {'─'*56}")
    print(f"  Képlet: Bookings = Impressions × CTR × CVR")
    print(f"  Képlet: ad_spend = Impressions × CPM / 1000 = {s.impressions:,.0f} × {s.cpm:,.0f} / 1000 = {r['ad_spend']:,.0f} Ft")
    print(f"          Bookings = Impressions × CTR × CVR = {s.impressions:,.0f} × {s.ctr*100:.1f}% × {s.cvr*100:.1f}% = {r['new_bookings_from_campaign']:,.0f} db")
    print(f"          CAC = ad_spend / new_bookings = {r['ad_spend']:,.0f} / {r['new_bookings_from_campaign']:,.0f} = {r['cac']:,.0f} Ft")
    print()
    print(f"  CPM = {s.cpm:,.0f} Ft  (ez az INPUT — mennyit fizetsz 1000 megjelenésért)")
    print(f"  Költség/megjelenés: {s.cpm/1000:.3f} Ft")
    print()
    print(f"  CTR = {s.ctr*100:.1f}%")
    if s.ctr < 0.01:
        print("    ❌ Alacsony CTR. A kreatív vagy célzás gyenge.")
        print("       Benchmark: wellness/beauty social adsban 1-2% tipikus.")
    elif s.ctr < 0.02:
        print("    ⚠️  Közepes CTR. Piac átlagán van.")
        print("       Javítható: erősebb FOMO-copy, időnyomás ('Ma este!'), lokáció.")
    else:
        print("    ✅ Erős CTR. A kreatív releváns és kattintható.")
    print()
    print(f"  CVR = {s.cvr*100:.1f}%  (kattintásból booking)")
    if s.cvr < 0.02:
        print("    ❌ Alacsony CVR. A landing page vagy az UX töri meg.")
        print("       Ok lehet: nincs elég ajánlat a közelben, vagy lassú betöltés.")
    elif s.cvr < 0.05:
        print("    ⚠️  Elfogadható CVR, de van tér javításra.")
        print("       Kulcskérdés: amit a user lát az appban releváns-e? Van slot?")
    else:
        print("    ✅ Erős CVR. A landing → booking flow súrlódásmentes.")
    print()
    print(f"  CAC (derived) = {r['cac']:,.0f} Ft")
    if r['cac'] > 8000:
        print("    ❌ Magas CAC. Minden új user megszerzése drága.")
        print("       Ha az LTV nem kompenzálja, a business elvérzik.")
    elif r['cac'] > 4000:
        print("    ⚠️  Közepes CAC. Megdolgoztatja a retention-t.")
        print("       Cél: organikus és referral csatornák bevonása csökkentéshez.")
    else:
        print("    ✅ Egészséges CAC. Paid csatorna hatékonyan működik.")
    print()
    print(f"  Hirdetési spend: {r['ad_spend']:,.0f} Ft / hó")
    print(f"  Ebből jön {r['new_bookings_from_campaign']:,.0f} új booking — ez a demand funnel 'bemenete'.")
    print(f"  FONTOS: Ez NEM azonos a teljes havi bookingokkal!")
    print(f"  A supply fill-rate modell a visszatérő usereket is beleszámolja.")


    # ── 2. SUPPLY ELEMZÉS ──────────────────────────────────────────
    print(f"\n  [2] SUPPLY & INVENTORY ELEMZÉS")
    print(f"  {'─'*56}")
    print(f"  Képlet: Össz. slot = Partners × Slot/nap × Napok")
    print(f"          {s.partners} × {s.idle_slots_per_partner_per_day} × {s.days_per_month} = {r['total_idle_slots_per_month']:,.0f} db/hó")
    print()
    print(f"  Aktív partnerek: {s.partners} db")
    print(f"    Megszerzésük: kb. 1000-2500 cold outreach → 20% válasz → 10% trial → 50% aktív marad.")
    print(f"    Szükséges outreach: ~{s.partners / 0.20 / 0.10 / 0.50:,.0f} megkeresés.")
    print()
    print(f"  Üres slot/partner/nap: {s.idle_slots_per_partner_per_day}")
    print(f"    Egy 4 terapeutás szalonban 70% occupancy mellett kb. 2-4 üres slot/nap reális.")
    print(f"    Ha ennél kevesebb: partner nem érzi a fájdalmat, nehéz meggyőzni.")
    print()
    print(f"  Fill rate: {s.fill_rate*100:.0f}%  →  Lefoglalt: {r['booked_slots_per_month']:,.0f} slot/hó")
    if s.fill_rate < 0.15:
        print("    ❌ Kritikusan alacsony. A platform nem hoz elég usert a slotokhoz.")
        print("       A partner kilép, mert 'nem működik'. Chicken-egg halál.")
    elif s.fill_rate < 0.30:
        print("    ⚠️  Gyenge liquidity. Nem mindig talál a user releváns slotot.")
        print("       Javítás: district-fókusz, kevesebb partner de sűrűbb coverage.")
    else:
        print("    ✅ Megfelelő fill rate. A platform értéket ad a partnernek.")
    print()
    print(f"  Diszkont: -{s.discount_depth*100:.0f}%  |  Eredeti ár: {s.aov:,.0f} Ft  →  Diszkontált: {r['discounted_price']:,.0f} Ft")
    print(f"    A {s.discount_depth*100:.0f}%-os diszkont:")
    print(f"      - Elég nagy, hogy a user impulzívan cselekedjen (pszichológiai trigger)")
    print(f"      - Elég kicsi, hogy a partner ne érezze brand-degradációnak")
    print(f"      - A partner contribution margin-ja még pozitív marad")

    # ── 3. GMV / REVENUE ELEMZÉS ──────────────────────────────────
    print(f"\n  [3] GMV & REVENUE ELEMZÉS")
    print(f"  {'─'*56}")
    print(f"  GMV = Lefoglalt slotok × Diszkontált ár")
    print(f"        {r['booked_slots_per_month']:,.0f} × {r['discounted_price']:,.0f} Ft = {r['gmv']:,.0f} Ft")
    print()
    print(f"  Revenue = GMV × Take rate = {r['gmv']:,.0f} × {s.take_rate*100:.0f}% = {r['revenue']:,.0f} Ft")
    print(f"    A {s.take_rate*100:.0f}%-os take rate indokolása:")
    print(f"      - Treatwell: ~20-25% (magas, erős brand)")
    print(f"      - ClassPass: ~15-20%")
    print(f"      - Korai fázisban {s.take_rate*100:.0f}% elfogadhatóbb a partner számára")
    print(f"      - Ha revenue-t növelnéd: take rate emelés kockázatos, inkább upsell")
    print()
    print(f"  Változó ktg — ops:   {r['variable_costs_ops']:,.0f} Ft  ({s.variable_cost_rate*100:.0f}% of revenue — payment/refund/support)")
    print(f"  Változó ktg — mktg: {r['variable_costs_marketing']:,.0f} Ft  (ad spend, CAC-alapú)")
    print(f"    Összetevők (ops): Stripe/payment ~2%, support ~1.5%, refund/fraud ~0.5%")
    print(f"    Marketing per booking: {r['marketing_cost_per_booking']:,.0f} Ft  (= ad_spend / össz. booked slot)")
    print()
    print(f"  Contribution margin: {r['contribution']:,.0f} Ft")
    print(f"  Contribution/booking: {r['contribution_per_booking']:,.0f} Ft")
    print(f"    Ez az az összeg, amivel minden egyes booking hozzájárul a fix költségek fedezéséhez.")
    cm_pct = r['contribution'] / r['revenue'] * 100 if r['revenue'] > 0 else 0
    health_str = 'jó' if cm_pct > 0 else 'negatív — a marketing spend meghaladja a revenue-t!'
    print(f"    Contribution margin %: {cm_pct:.1f}% — {health_str}")

    # ── 4. RETENTION / LTV ELEMZÉS ────────────────────────────────
    print(f"\n  [4] RETENTION & LTV ELEMZÉS")
    print(f"  {'─'*56}")
    print(f"  Képlet: LTV = (f / churn) × AOV × take_rate × (1 - var_cost)")
    print(f"          ({s.bookings_per_user_per_month} / {s.monthly_churn}) × {s.aov:,.0f} × {s.take_rate} × {1-s.variable_cost_rate}")
    print(f"          = {r['lifetime_bookings']:.1f} booking × {r['revenue_per_booking']:,.0f} Ft = {r['ltv']:,.0f} Ft")
    print()
    print(f"  Havi churn: {s.monthly_churn*100:.0f}%  →  Élettartam: {r['lifetime_months']:.1f} hónap")
    if s.monthly_churn > 0.30:
        print("    ❌ Magas churn. A userek hamar elhagyják a platformot.")
        print("       Ok lehet: nincs mindig slot a közelben, rossz élmény, egyszer kipróbálták.")
    elif s.monthly_churn > 0.18:
        print("    ⚠️  Közepes churn. Valódi wellness habit még nem alakult ki.")
        print("       Javítás: push notifikáció ('új slot a közeledben!'), hűségprogram, reminder.")
    else:
        print("    ✅ Alacsony churn. A platform napi rutinba épül.")
    print()
    print(f"  Havi booking frekvencia: {s.bookings_per_user_per_month}/user")
    print(f"    Benchmark: Treatwell ~1.2/hó, ClassPass ~3-4/hó (gym-alapú, magasabb freq.)")
    print(f"    Wellness/masszázs: 1.5 reális — ez havonta kb. 1-2 alkalom.")
    print()
    print(f"  LTV: {r['ltv']:,.0f} Ft")
    if r['ltv'] < 8000:
        print("    ❌ Kritikusan alacsony LTV. A business nem tudja visszatermelni a CAC-ot.")
    elif r['ltv'] < 15000:
        print("    ⚠️  Gyenge LTV. A megtérülés bizonytalan.")
    else:
        print("    ✅ Egészséges LTV. A visszatérő userek értéket teremtenek.")

    # ── 5. LTV/CAC ELEMZÉS ────────────────────────────────────────
    print(f"\n  [5] LTV/CAC — A LEGFONTOSABB MUTATÓ")
    print(f"  {'─'*56}")
    ratio = r['ltv_cac']
    print(f"  LTV/CAC = {r['ltv']:,.0f} Ft / {r['cac']:,.0f} Ft = {ratio:.2f}x")
    print()
    if ratio < 1:
        print("  ❌ KRITIKUS: Minden egyes userre pénzt veszítesz összességében.")
        print("     A business jelenlegi formájában nem skálázható.")
        print("     Azonnal kezelendő: churn csökkentés VAGY CAC csökkentés.")
    elif ratio < 2:
        print("  ⚠️  GYENGE: A margin minimális, semmilyen hiba nem fér bele.")
        print(f"     {ratio:.2f}x azt jelenti: 1 Ft CAC-ra {ratio:.2f} Ft LTV jön vissza.")
        print("     Javítandó: organikus forgalom növelése (SEO, referral, push).")
    elif ratio < 3:
        print("  ⚠️  ELFOGADHATÓ, DE NEM JÓ: Seed-szinten belefér, de Series A előtt javítani kell.")
        print("     A 3x a minimális VC benchmark. Ez alatt nehéz tőkét bevonni.")
    else:
        print("  ✅ EGÉSZSÉGES: Minden befektetett CAC legalább 3x-osan térül meg.")
        print("     Ez az a szint, ahol a marketing spend-et érdemes agresszívan növelni.")
    print()
    print(f"  Mit kell megváltoztatni {ratio:.2f}x → 3x eléréséhez?")
    target_ltv = 3 * r['cac']
    target_cac = r['ltv'] / 3
    print(f"    Opció A: LTV növelés → szükséges LTV: {target_ltv:,.0f} Ft (jelenlegi: {r['ltv']:,.0f} Ft)")
    print(f"             Churn csökkentése {s.monthly_churn*100:.0f}% → {s.monthly_churn*0.7*100:.0f}%-ra hozná el.")
    print(f"    Opció B: CAC csökkentés → szükséges CAC: {target_cac:,.0f} Ft (jelenlegi: {r['cac']:,.0f} Ft)")
    print(f"             Organikus/referral csatorna bevonása csökkenti a paid függőséget.")

    # ── 6. PARTNER ECONOMICS ──────────────────────────────────────
    print(f"\n  [6] PARTNER ECONOMICS ELEMZÉS")
    print(f"  {'─'*56}")
    print(f"  Mit kap egy átlagos partner tőled havonta?")
    print(f"  Inkrementális bevétel: {r['incremental_revenue_per_partner']:,.0f} Ft")
    print(f"  Ebből jutalék:         {r['commission_per_partner']:,.0f} Ft  ({s.take_rate*100:.0f}%)")
    print(f"  Nettó partner nyereség:{r['partner_net_gain']:,.0f} Ft")
    print()
    monthly_idle_value_lost = s.idle_slots_per_partner_per_day * s.days_per_month * s.aov
    print(f"  Elveszett bevétel nélküled (idle × normál ár): {monthly_idle_value_lost:,.0f} Ft/hó")
    print(f"  Te ebből {r['incremental_revenue_per_partner']/monthly_idle_value_lost*100:.1f}%-ot mentesz meg.")
    print()
    if r['partner_net_gain'] < 100_000:
        print("  ❌ A partner nyeresége alacsony. Nehéz lesz megtartani őket.")
        print("     Átgondolandó: alacsonyabb jutalék, vagy magasabb fill rate.")
    elif r['partner_net_gain'] < 300_000:
        print("  ⚠️  A partner nyeresége közepes. Kellemes bónusz, de nem game-changer.")
        print("     Cél: 300k+ Ft nettó/hó — ott kezd 'must have' lenni a partner számára.")
    else:
        print("  ✅ A partner jelentős extra bevételt kap. Churn valószínűtlen.")

    # ── 7. BREAK-EVEN ELEMZÉS ─────────────────────────────────────
    print(f"\n  [7] BREAK-EVEN ELEMZÉS")
    print(f"  {'─'*56}")
    print(f"  Képlet: Break-even = Fix ktg / Contribution per booking")
    print(f"          {r['total_fixed_costs']:,.0f} Ft / {r['contribution_per_booking']:,.0f} Ft = {r['breakeven_bookings']:,.0f} booking/hó")
    print()
    print(f"  Fix költségek bontása (valóban fix):")
    print(f"    Bérek:        {s.payroll:>12,.0f} Ft  ({s.payroll/r['total_fixed_costs']*100:.0f}%)")
    print(f"    Infra:        {s.infra:>12,.0f} Ft  ({s.infra/r['total_fixed_costs']*100:.0f}%)")
    print(f"    Support:      {s.support_fixed:>12,.0f} Ft  ({s.support_fixed/r['total_fixed_costs']*100:.0f}%)")
    print(f"    ÖSSZESEN:     {r['total_fixed_costs']:>12,.0f} Ft")
    print(f"  + Változó (marketing): {r['variable_costs_marketing']:>10,.0f} Ft  (ad spend, már levonva a contribution-ből)")
    print()
    be_gap = r['booked_slots_per_month'] - r['breakeven_bookings']
    be_pct = r['booked_slots_per_month'] / r['breakeven_bookings'] * 100 if r['breakeven_bookings'] > 0 else 0
    print(f"  Jelenlegi szint: {r['booked_slots_per_month']:,.0f} booking = a break-even {be_pct:.0f}%-a")
    if be_gap >= 0:
        print(f"  ✅ Profitábilis: {be_gap:,.0f} bookingos pufferrel break-even felett.")
    else:
        partners_needed = abs(be_gap) / (s.idle_slots_per_partner_per_day * s.days_per_month * s.fill_rate)
        print(f"  ❌ {abs(be_gap):,.0f} booking hiányzik a nullszaldóhoz.")
        print(f"     Ez kb. {partners_needed:.0f} további aktív partnert jelent.")
        print(f"     VAGY: fill rate {s.fill_rate*100:.0f}% → {r['breakeven_bookings']/r['total_idle_slots_per_month']*100:.0f}%-ra kellene nőnie.")
    print()
    print(f"  Havi veszteség/nyereség: {r['profit']:,.0f} Ft")
    if r['profit'] < 0:
        print(f"  Ez azt jelenti: {abs(r['profit']):,.0f} Ft/hó cash burn.")
        print(f"  10M Ft seed pénznél: ~{10_000_000/abs(r['profit']):.1f} hónap runway.")

    # ── 8. SZINTÉZIS ──────────────────────────────────────────────
    print(f"\n  [8] SZINTÉZIS — MI A 3 LEGFONTOSABB LEVER?")
    print(f"  {'─'*56}")
    levers = [
        ("Fill rate növelés",
         f"{s.fill_rate*100:.0f}% → 40%",
         f"GMV: {r['booked_slots_per_month']/s.fill_rate*0.40*r['discounted_price']/1_000_000:.1f}M Ft"),
        ("Churn csökkentés",
         f"{s.monthly_churn*100:.0f}% → 15%",
         f"LTV: {(s.bookings_per_user_per_month/0.15)*s.aov*s.take_rate*(1-s.variable_cost_rate):,.0f} Ft"),
        ("Partner szám növelés",
         f"{s.partners} → 100 partner",
         f"GMV: {100*s.idle_slots_per_partner_per_day*s.days_per_month*s.fill_rate*r['discounted_price']/1_000_000:.1f}M Ft"),
    ]
    for i, (name, change, impact) in enumerate(levers, 1):
        print(f"  {i}. {name}: {change}  →  {impact}")
    print()
    print(f"  A legkritikusabb: FILL RATE.")
    print(f"  Ha a user belép és nem lát releváns slotot → uninstall.")
    print(f"  Ha a partner feltölt és nem jön booking → churn.")
    print(f"  A fill rate a marketplace két oldalát köti össze — ez a 'szívverés'.")
    print(f"\n{'#'*60}\n")


# ─────────────────────────────────────────────
# SZCENÁRIÓK DEFINIÁLÁSA
# ─────────────────────────────────────────────

scenarios: List[Scenario] = [

    Scenario(
        name="🐣 MVP / Korai fázis",
        impressions=200_000,
        cpm=2_000,          # Meta HU tipikus
        ctr=0.012,
        cvr=0.03,
        aov=15_000,
        take_rate=0.12,
        variable_cost_rate=0.05,
        bookings_per_user_per_month=1.2,
        monthly_churn=0.30,
        partners=20,
        idle_slots_per_partner_per_day=2.0,
        discount_depth=0.30,
        fill_rate=0.20,
        payroll=400_000,
        marketing_fixed=0,
        infra=150_000,
        support_fixed=200_000,
    ),

    Scenario(
        name="📈 Növekedési fázis (50 partner)",
        impressions=600_000,
        cpm=1_000,         # 1 Ft/megjelenés (Meta HU reális 1500-3000, TikTok ~171)
        ctr=0.025,         # erős kreatív
        cvr=0.06,          # jól konvertáló landing
        aov=15_000,
        take_rate=0.15,
        variable_cost_rate=0.04,
        bookings_per_user_per_month=1.5,
        monthly_churn=0.22,
        partners=30,
        idle_slots_per_partner_per_day=2.5,
        discount_depth=0.30,
        fill_rate=0.35,
        payroll=400_000,
        marketing_fixed=0,
        infra=200_000,
        support_fixed=200_000,
    ),

    Scenario(
        name="🔬 Kutatás-alapú (2025 Benchmark)",
        impressions=1_000_000,
        cpm=2_000,         # Meta HU realitás
        ctr=0.022,         # 30% off FOMO hatása
        cvr=0.015,         # App-letöltős funnel (sajnos ennyi)
        aov=15_000,
        take_rate=0.12,
        variable_cost_rate=0.02, # Barion/SimplePay optimalizáció
        bookings_per_user_per_month=1.3, # Reális masszázs frekvencia
        monthly_churn=0.30, # App retention realitás
        partners=50,
        idle_slots_per_partner_per_day=6.0, # Kutatás szerinti 60% occupancy
        discount_depth=0.30,
        fill_rate=0.15,    # Alacsonyabb fill rate a nagy inventory miatt
        payroll=0,
        marketing_fixed=0,
        infra=50_000,
        support_fixed=50_000,
    ),

    Scenario(
        name="🔬 Kutatás + Stratégiai Pivot",
        impressions=400_000/2.5, # Kevesebb, de minőségibb elérés
        cpm=2_200,          # Kicsit drágább, fókuszáltabb célzás
        ctr=0.025,          # Optimalizált kreatívok
        cvr=0.045,          # WEB-FIRST (nincs app letöltési súrlódás!)
        aov=15_000,         # Kicsit több prémium partner
        take_rate=0.20,     # Inkrementális bevételért cserébe reális a 20%
        variable_cost_rate=0.02,
        bookings_per_user_per_month=1.4,
        monthly_churn=0.21, # CRM és lojalitás program hatása
        partners=20,        # Sűrűbb hálózat a kerületekben
        idle_slots_per_partner_per_day=3.5,
        discount_depth=0.30,
        fill_rate=0.20,     # Jobb likviditás a webes felület miatt
        payroll=0,          # Marad a te beállításod
        marketing_fixed=0,
        infra=50_000,
        support_fixed=50_000,
    ),

    Scenario(
        name="🚀 Érett piac (100 partner, Budapest)",
        impressions=1_500_000,
        cpm=2_000,
        ctr=0.018,
        cvr=0.05,
        aov=16_000,
        take_rate=0.12,
        variable_cost_rate=0.04,
        bookings_per_user_per_month=1.8,
        monthly_churn=0.18,
        partners=100,
        idle_slots_per_partner_per_day=2.5,
        discount_depth=0.28,
        fill_rate=0.35,
        payroll=5_000_000,
        marketing_fixed=3_000_000,
        infra=500_000,
        support_fixed=800_000,
    ),

    Scenario(
        name="🌍 Regionális (Budapest + Bécs)",
        impressions=4_000_000,
        cpm=2_000,
        ctr=0.016,
        cvr=0.045,
        aov=18_000,
        take_rate=0.13,
        variable_cost_rate=0.04,
        bookings_per_user_per_month=2.0,
        monthly_churn=0.15,
        partners=200,
        idle_slots_per_partner_per_day=2.5,
        discount_depth=0.25,
        fill_rate=0.40,
        payroll=10_000_000,
        marketing_fixed=8_000_000,
        infra=1_000_000,
        support_fixed=2_000_000,
    ),

    Scenario(
        name="😰 Pesszimista (gyenge retention, alacsony fill)",
        impressions=500_000,
        cpm=1_500,
        ctr=0.010,
        cvr=0.025,
        aov=13_000,
        take_rate=0.10,
        variable_cost_rate=0.06,
        bookings_per_user_per_month=1.0,
        monthly_churn=0.40,
        partners=30,
        idle_slots_per_partner_per_day=1.5,
        discount_depth=0.35,
        fill_rate=0.12,
        payroll=2_000_000,
        marketing_fixed=1_000_000,
        infra=200_000,
        support_fixed=300_000,
    ),

    Scenario(
        name="🌟 Optimista (erős brand, high repeat)",
        impressions=2_000_000,
        cpm=2_000,
        ctr=0.022,
        cvr=0.06,
        aov=17_000,
        take_rate=0.14,
        variable_cost_rate=0.03,
        bookings_per_user_per_month=2.2,
        monthly_churn=0.12,
        partners=120,
        idle_slots_per_partner_per_day=3.0,
        discount_depth=0.25,
        fill_rate=0.45,
        payroll=6_000_000,
        marketing_fixed=4_000_000,
        infra=600_000,
        support_fixed=1_000_000,
    ),
]


# ─────────────────────────────────────────────
# ÖSSZEHASONLÍTÓ TÁBLÁZAT
# ─────────────────────────────────────────────

def print_comparison(scenarios: List[Scenario]):
    print(f"\n{'═'*90}")
    print("  ÖSSZEHASONLÍTÓ TÁBLÁZAT")
    print(f"{'═'*90}")
    header = f"{'Szcenárió':<35} {'GMV/hó':>12} {'Rev/hó':>12} {'Profit':>12} {'LTV/CAC':>8} {'Fill%':>7}"
    print(header)
    print("─" * 90)
    for s in scenarios:
        r = simulate(s)
        ltv_cac_str = f"{r['ltv_cac']:.2f}x"
        profit_sign = "+" if r["profit"] >= 0 else ""
        print(
            f"  {s.name:<33} "
            f"{r['gmv']/1_000_000:>9.1f}M Ft "
            f"{r['revenue']/1_000_000:>9.1f}M Ft "
            f"{profit_sign}{r['profit']/1_000_000:>8.1f}M Ft "
            f"{ltv_cac_str:>8} "
            f"{s.fill_rate*100:>6.0f}%"
        )
    print(f"{'═'*90}\n")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "═" * 60)
    print("  LAST-MINUTE WELLNESS MARKETPLACE — SCENARIO SIMULATOR")
    print("  Növekedési fázis — részletes elemzés")
    print("═" * 60)

    # Futtassuk le a stratégiai pivot szcenáriót
    pivot = [s for s in scenarios if "Pivot" in s.name][0]
    r = simulate(pivot)
    print_scenario(pivot, r)
    #analyze_scenario(pivot, r)

    print("💡 Tipp: Módosítsd a Scenario() paramétereket a saját becsléseidhez!")
    print("   A változók magyarázata a kód tetején (ADATSTRUKTÚRA szekcióban) megtalálható.\n")
