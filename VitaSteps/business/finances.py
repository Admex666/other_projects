import pandas as pd

# =========================
# 1) INPUTS – ITT ÁLLÍTSD BE
# =========================

months = 12

scenarios = {
    "base": {
        "price_per_unit": 8490,              # eladási ár / db
        "units_sold_per_month": 35,       # havi darabszám
        "material_cost_per_unit": 1756*1.3,      # anyagköltség / db
        "production_cost_per_unit": 0,    # gyártás / db
        "packaging_shipping_per_unit": 1500, # csomagolás + szállítás / db
        
        "fixed_costs_per_month": 30000,      # fix költségek
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
        "fixed_costs_per_month": 25000,
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
        "fixed_costs_per_month": 30_000,
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