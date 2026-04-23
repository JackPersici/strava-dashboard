from __future__ import annotations

from pathlib import Path
import pandas as pd


def ensure_data_dir(path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def save_activities(df: pd.DataFrame, path: str) -> None:
    ensure_data_dir(path)
    df.to_parquet(path, index=False)


def load_activities(path: str) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        return pd.DataFrame()
    return pd.read_parquet(p)
