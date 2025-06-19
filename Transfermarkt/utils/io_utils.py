import pandas as pd

def save_df(df, path):
    df.to_csv(path, index=False)
    print(f"Saved to {path}")
