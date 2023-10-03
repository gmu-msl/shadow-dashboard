import pandas as pd
import numpy as np


def cast_col(col: pd.Series) -> pd.Series:
    if col.dtype == 'object':
        if all([is_float(x) for x in col]):
            return col.astype(float)
        elif all([is_int(x) for x in col]):
            return col.astype(float)
        elif all([is_date(x) for x in col]):
            return pd.Series(pd.to_datetime(col)).astype(float)
        else:
            return col.astype(str)
    elif np.issubdtype(col.dtype, np.datetime64):
        return col.astype(np.int64)
    else:
        return col.astype(float)


def is_float(s: str) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        return False


def is_int(s: str) -> bool:
    try:
        int(s)
        return True
    except ValueError:
        return False


def is_date(s: str) -> bool:
    try:
        pd.to_datetime(s)
        return True
    except ValueError:
        return False


def cast_columns(df):
    for col in df.columns:
        df[col] = cast_col(df[col])
    return df
