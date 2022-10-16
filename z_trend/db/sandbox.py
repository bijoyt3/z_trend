import pandas as pd


def resample(df: pd.DataFrame):
    df_ = df.resample('W', on='LastUpdated') \
        .agg({'ListedPrice': 'mean', 'zpid': 'nunique'}) \
        .astype(int) \
        .reset_index() \
        .rename(columns={'ListedPrice': '{}_price'.format(str(df)), 'zpid':''})

    return df_

