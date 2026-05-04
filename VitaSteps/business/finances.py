import pandas as pd

# =========================
# 1) INPUTS – ITT ÁLLÍTSD BE
# =========================
# ADÓZÁSI MEGJEGYZÉS (Laci, 2026.05.04.):
# - 0-3.5M Ft bevételig: NINCS SZJA vonzat (másodállású átalányadó)
# - Egyetlen fix adóteher: Helyi Iparűzési Adó (IPA) max 50.000 Ft/év = ~4.167 Ft/hó
# - Import ÁFA (27%): beépítve a material_cost_per_unit *1.3 szorzóba
# - DDP szállítás esetén a vám + import ÁFA Kimmi áraiban szerepel (tisztázandó!)

months = 12

scenarios = {
    "base": {
        "price_per_unit": 8490,              # eladási ár / db
        "units_sold_per_month": 35,       # havi darabszám
        "material_cost_per_unit": 1756*1.3,      # anyagköltség / db
        "production_cost_per_unit": 0,    # gyártás / db
        "packaging_shipping_per_unit": 1500, # csomagolás + szállítás / db
        
        "fixed_costs_per_month": 30000 + 4167,  # fix költségek (könyvelő 30k + IPA ~4167 Ft/hó)
        "marketing_per_month": 25000,        # marketing
        
        "customer_payment_delay": 0,        # hónap (bevétel késleltetés)
        "supplier_payment_delay": 0,        # hónap
        
        "initial_cash": 0               # kezdő pénz
    },

    "optimistic": {
        "price_per_unit": 8990,
        "units_sold_per_month": 75,
        "material_cost_per_unit": 1756*1.3,
        "production_cost_per_unit": 0,
        "packaging_shipping_per_unit": 1300,
        "fixed_costs_per_month": 25000 + 4167,  # könyvelő 25k + IPA
        "marketing_per_month": 20000,
        "customer_payment_delay": 0,
        "supplier_payment_delay": 0,
        "initial_cash": 0
    },

    "pessimistic": {
        "price_per_unit": 7990,
        "units_sold_per_month": 15,
        "material_cost_per_unit": 1756*1.3,
        "production_cost_per_unit": 0,
        "packaging_shipping_per_unit": 1700,
        "fixed_costs_per_month": 30_000 + 4167,  # könyvelő 30k + IPA
        "marketing_per_month": 30_000,
        "customer_payment_delay": 0,
        "supplier_payment_delay": 0,
        "initial_cash": 0
    }
}


# =========================
# 2) SZÁMÍTÁSOK
# =========================

def run_scenario(params):
    df = pd.DataFrame({"month": range(1, months+1)})

    # Árbevétel
    df["revenue"] = params["price_per_unit"] * params["units_sold_per_month"]

    # Költségek
    unit_cost = (
        params["material_cost_per_unit"]
        + params["production_cost_per_unit"]
        + params["packaging_shipping_per_unit"]
    )

    df["cogs"] = unit_cost * params["units_sold_per_month"]
    df["gross_profit"] = df["revenue"] - df["cogs"]

    df["fixed_costs"] = params["fixed_costs_per_month"]
    df["marketing"] = params["marketing_per_month"]

    df["operating_profit"] = df["gross_profit"] - df["fixed_costs"] - df["marketing"]

    # =========================
    # CASHFLOW
    # =========================

    df["cash_in"] = df["revenue"].shift(params["customer_payment_delay"]).fillna(0)
    df["cash_out"] = (
        df["cogs"].shift(params["supplier_payment_delay"]).fillna(0)
        + df["fixed_costs"]
        + df["marketing"]
    )

    df["net_cashflow"] = df["cash_in"] - df["cash_out"]

    # Készpénz egyenleg
    cash = params["initial_cash"]
    cash_balance = []

    for cf in df["net_cashflow"]:
        cash += cf
        cash_balance.append(cash)

    df["cash_balance"] = cash_balance

    return df


# =========================
# 3) FUTTATÁS
# =========================

results = {}

for name, params in scenarios.items():
    results[name] = run_scenario(params)

# =========================
# 4) BREAK-EVEN SZÁMÍTÁS
# =========================

def break_even_units(params):
    unit_cost = (
        params["material_cost_per_unit"]
        + params["production_cost_per_unit"]
        + params["packaging_shipping_per_unit"]
    )

    contribution_margin = params["price_per_unit"] - unit_cost

    if contribution_margin <= 0:
        return None

    return (params["fixed_costs_per_month"] + params["marketing_per_month"]) / contribution_margin


# =========================
# 5) OUTPUT
# =========================

for name, df in results.items():
    print(f"\n=== {name.upper()} SCENARIO ===")
    print(df[["month", "revenue", "operating_profit", "net_cashflow", "cash_balance"]])

    be = break_even_units(scenarios[name])
    print(f"\nBreak-even (db/hó): {round(be, 0) if be else 'N/A'}")

    annual_revenue = df["revenue"].sum()
    annual_profit = df["operating_profit"].sum()
    ipa = min(annual_revenue * 0.02, 50000)  # IPA: 2%, max 50k Ft/év
    print(f"Éves árbevétel: {annual_revenue:,.0f} Ft")
    print(f"Éves működési profit (IPA előtt): {annual_profit:,.0f} Ft")
    print(f"Helyi Iparűzési Adó (IPA): {ipa:,.0f} Ft/év")
    print(f"Becsült éves SZJA: 0 Ft (3,5M Ft alatt másodállású átalányadóval)" if annual_revenue <= 3_500_000 else f"Figyelem: 3,5M Ft felett SZJA is keletkezik! Konzultálj Lacival.")