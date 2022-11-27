from __future__ import annotations
import fuzzywuzzy.process
import itertools
from pathlib import Path
import pandas as pd

from ivchecker.configuration import Config

# path to the root folder
ROOT = Path(__file__).parent.parent.resolve()

#
STAT_NAMES = ("HP", "Atk", "Def", "SpA", "SpD", "Spe")

# configuration object
config = Config.from_yaml(ROOT / "config.yaml")

# helper type alias
SixInts = tuple[int, int, int, int, int, int]
SixFloats = tuple[float, float, float, float, float, float]

NATURE_MODIFIER = 0.1


def flatten_one_level(nested):
    return itertools.chain.from_iterable(nested)


def fuzzy(target: str, options: list[str], limit: int) -> list[str]:
    """Return the n closest values in the options."""
    matches = [option for option, _ in fuzzywuzzy.process.extract(target, options)]
    return matches[:limit]

def search_dataframe(df: pd.DataFrame, column: str, value: str):
    found = df[df[column].str.lower() == value.lower()]
    
    if found.empty:
        raise ValueError(f"could not find value: {value}")
    
    return flatten_one_level(found.values)

def format_ivs(ivs) -> str:
    """ Format a range. [] -> "", [3] -> "3", [4, 5, 6] -> "4-6" """
    if len(ivs) == 0:
        return "ERROR"

    if len(ivs) == 1:
        return str(ivs[0])

    res = f"{min(ivs)}-{max(ivs)}"
    if all(iv & 1 == 0 for iv in ivs):
        res += " (even)"
    elif all(iv & 1 == 1 for iv in ivs):
        res += " (odd)"

    return res
