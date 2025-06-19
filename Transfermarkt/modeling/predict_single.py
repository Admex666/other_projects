import pandas as pd
import numpy as np
from config import PATH_MERGED
from utils.io_utils import save_df

def predict_future_value(model, preprocessor, df):
    # 2. Feature szűrés (a preprocessor által használt feature-ökre)
    X = df.copy()
    X_proc = preprocessor.transform(X)

    # 3. Predikció
    preds = model.predict(X_proc)

    # 4. Predikció mentése
    df['predicted_value'] = preds

    # 5. Opció: növekedési százalék és különbség kiszámítása
    df['value_change'] = df['predicted_value'] - df['marketValue']
    df['value_pct_change'] = (df['value_change'] / df['marketValue']) * 100

    return df[['player_', 'marketValue', 'predicted_value', 'value_change', 'value_pct_change']]
