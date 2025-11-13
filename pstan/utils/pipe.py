import pandas as pd
from typing import Any

class dotdict(dict):
    """dot.access to dictionary attributes"""
    def __getattr__(self, key: str) -> Any:
        return self.get(key)

    def __setattr__(self, key: str, value: Any) -> None:
        self[key] = value

    def __delattr__(self, key: str) -> None:
        del self[key]

def pipe(df: pd.DataFrame, **processors: Any) -> tuple[pd.DataFrame, Any]:
    for p in processors.values(): df = p.process(df)
    return df, dotdict(processors)
