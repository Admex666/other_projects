from PenzugyiElemzo import PenzugyiElemzo
                    
#%% =====================
# ELEMZÉS FUTTATÁSA
# =====================
df = pd.read_csv('szintetikus_tranzakciok.csv')
# 1. Osztály példányosítása
elemzo = PenzugyiElemzo(df)

# 2. Átfogó jelentés generálása egy felhasználóra (itt user_id=1)
jelentes = elemzo.generate_comprehensive_report(48)

from pprint import pprint

print("🌟 Executive Summary:")
pprint(jelentes["executive_summary"], indent=2, width=100)

print("\n💸 Cash Flow Elemzés:")
pprint(jelentes["cash_flow_elemzes"], indent=2, width=100)

print("\n💡 Spórolási Lehetőségek:")
pprint(jelentes["sporolas_optimalizacio"], indent=2, width=100)


