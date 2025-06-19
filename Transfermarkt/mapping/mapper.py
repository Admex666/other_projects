import pandas as pd
from config import PATH_MAPPING

def load_mapping():
    return pd.read_csv(PATH_MAPPING, encoding='latin1')

def is_in_mapping(mapping_df, player_id):
    return (mapping_df.tm_id == int(player_id)).any()
