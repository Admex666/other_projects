from UserFinancialEDA import UserFinancialEDA, run_user_eda
import pandas as pd

# Példa használat:
df = pd.read_csv('szintetikus_tranzakciok.csv')
eredmenyek = run_user_eda(df, 40)