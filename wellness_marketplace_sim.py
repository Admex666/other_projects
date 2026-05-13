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
    impressions: float = 1_000_000        # megjelenések száma
    ctr: float = 0.015                    # click-through rate (pl. 0.015 = 1.5%)
    cpc: float = 250                      # cost per click (Ft)
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
    clicks = s.impressions * s.ctr
    ad_spend = clicks * s.cpc
    new_bookings = clicks * s.cvr           # first bookings (= new users kb.)
    cac = s.cpc / s.cvr if s.cvr > 0 else float("inf")

    r["clicks"] = clicks
    r["ad_spend"] = ad_spend
    r["new_bookings_from_campaign"] = new_bookings
    r["cac"] = cac

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
    variable_costs = revenue * s.variable_cost_rate
    contribution = revenue - variable_costs
    contribution_per_booking = contribution / booked_slots if booked_slots > 0 else 0

    r["gmv"] = gmv
    r["revenue"] = revenue
    r["variable_costs"] = variable_costs
    r["contribution"] = contribution
    r["contribution_per_booking"] = contribution_per_booking

    # --- LTV ---
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

    # --- FIXED COSTS & BREAK-EVEN ---
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
    print(f"  CTR:                   {fmt(s.ctr, '%')}")
    print(f"  Kattintások:           {fmt(r['clicks'], 'db')}")
    print(f"  CPC:                   {fmt(s.cpc)}")
    print(f"  Hirdetési költség:     {fmt(r['ad_spend'])}")
    print(f"  Booking CVR:           {fmt(s.cvr, '%')}")
    print(f"  Új bookingok:          {fmt(r['new_bookings_from_campaign'], 'db')}")
    print(f"  CAC:                   {fmt(r['cac'])}  {health(1/r['cac']*10000, 2, 1)}")

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
    print(f"  Változó ktg:           {fmt(r['variable_costs'])}  ({fmt(s.variable_cost_rate, '%')} of rev)")
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
    print("  🏗️  FIXED COSTS & BREAK-EVEN")
    print(f"{'─'*60}")
    print(f"  Bérek:                 {fmt(s.payroll)}")
    print(f"  Marketing büdzsé:      {fmt(s.marketing_fixed)}")
    print(f"  Infra:                 {fmt(s.infra)}")
    print(f"  Support:               {fmt(s.support_fixed)}")
    print(f"  Összes fix ktg/hó:    {fmt(r['total_fixed_costs'])}")
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
# SZCENÁRIÓK DEFINIÁLÁSA
# ─────────────────────────────────────────────

scenarios: List[Scenario] = [

    Scenario(
        name="🐣 MVP / Korai fázis",
        impressions=200_000,
        ctr=0.012,
        cpc=280,
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
        payroll=1_500_000,
        marketing_fixed=500_000,
        infra=150_000,
        support_fixed=200_000,
    ),

    Scenario(
        name="📈 Növekedési fázis (50 partner)",
        impressions=600_000,
        ctr=0.015,
        cpc=260,
        cvr=0.04,
        aov=15_000,
        take_rate=0.12,
        variable_cost_rate=0.04,
        bookings_per_user_per_month=1.5,
        monthly_churn=0.22,
        partners=50,
        idle_slots_per_partner_per_day=2.0,
        discount_depth=0.30,
        fill_rate=0.28,
        payroll=3_000_000,
        marketing_fixed=1_500_000,
        infra=300_000,
        support_fixed=400_000,
    ),

    Scenario(
        name="🚀 Érett piac (100 partner, Budapest)",
        impressions=1_500_000,
        ctr=0.018,
        cpc=240,
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
        ctr=0.016,
        cpc=300,
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
        ctr=0.010,
        cpc=320,
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
        ctr=0.022,
        cpc=220,
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
    print("  Képletek és hipotézisek számszerűsítése")
    print("═" * 60)

    for s in scenarios:
        r = simulate(s)
        print_scenario(s, r)

    print_comparison(scenarios)

    print("💡 Tipp: Módosítsd a Scenario() paramétereket a saját becsléseidhez!")
    print("   A változók magyarázata a kód tetején (ADATSTRUKTÚRA szekcióban) megtalálható.\n")
