import pandas as pd
from MLinsight import MLinsight

df = pd.read_csv('szintetikus_tranzakciok.csv')

MLinsight(df, 20)
