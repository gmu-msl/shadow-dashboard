import pandas as pd


def df_to_ts(df):
    df.loc[:, 'count'] = 1
    if not isinstance(df.index, pd.DatetimeIndex):
        print(df)
    # tmp = df.resample('100ms').sum(numeric_only=True).infer_objects()
    tmp = df.resample('3333ms').sum(numeric_only=True).infer_objects()
    tmp = tmp.reset_index()
    return tmp
