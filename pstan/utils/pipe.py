import pandas as pd

def pipe(df: pd.DataFrame, **processors):

    class dotdict(dict):
        """dot.access to dictionary attributes"""
        __getattr__ = dict.get
        __setattr__ = dict.__setitem__
        __delattr__ = dict.__delitem__

    for p in processors.values(): df = p.process(df)
    return df, dotdict(processors)
