from __future__ import annotations
from contextlib import suppress
from dataclasses import dataclass
from enum import Enum
import fuzzywuzzy.process
import itertools
from math import isclose
from pathlib import Path
import pandas as pd
from typing import Iterator

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
    matches = [option for option,
               _ in fuzzywuzzy.process.extract(target, options)]
    return matches[:limit]


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


def get_all_pokemon() -> list[str]:
    data = pd.read_csv(ROOT / config.paths.basestats)
    return data["Name"].tolist()


def fuzzy_match_pokemon(pokemon: str, num: int = 2) -> tuple[str]:
    options = get_all_pokemon()
    matches = [p for p, _ in fuzzywuzzy.process.extract(pokemon, options)]
    return tuple(str(p) for p in matches[:num])


def _get_modern_basestats(pokemon: str) -> SixInts:
    """ Get the most recent basestats for the given Pokémon. """
    data = pd.read_csv(ROOT / config.paths.basestats)
    filtered = data[data["Name"].str.lower() == pokemon.lower()]

    if filtered.empty:
        # could not find the pokemon
        p, q = fuzzy_match_pokemon(pokemon, 2)
        raise ValueError(
            f"Could not find base stats for {pokemon!r}.\nDid you mean {p} or {q}?")

    # bs.values = [[name, HP, Atk, Def, SpA, SpD, Spe]]
    _, *stats = filtered.values[0]
    return tuple(stats)


def _get_stat_changes(pokemon: str) -> dict[int, SixInts]:
    """ Get all known stat changes for the given Pokémon, by generation. """
    data = pd.read_csv(ROOT / config.paths.statchanges)
    filtered = data[data.Pokemon.str.lower() == pokemon.lower()]

    return {gen: tuple(stats) for _, _, gen, *stats in filtered.values}


def get_basestats(pokemon: str, generation: int = config.generations.most_recent) -> SixInts:
    """ Return the base stats for the given Pokemon in the given generation. """
    modern_stats = _get_modern_basestats(pokemon)

    if generation == config.generations.most_recent:
        # We're good to just return these stats.
        return modern_stats

    changes = _get_stat_changes(pokemon)
    if not changes:
        # This Pokémon doesn't have any registered changes,
        # so once again, we can just return the modern stats.
        return modern_stats

    # Otherwise, there are changes we need to undo.
    for g in range(config.generations.most_recent, generation - 1, -1):
        with suppress(KeyError):
            return changes[g]

    # The stat changes were long ago and don't affect us.
    return modern_stats


@dataclass
class Nature:
    name: str
    raised: str
    lowered: str

    @classmethod
    def from_name(cls, name: str) -> Nature:
        df = pd.read_csv(ROOT / config.paths.natures)
        found = df[df["Name"].str.lower() == name.lower()]

        if found.empty:
            # could not find the nature
            raise ValueError(f"Could not find nature {name!r}")

        # found.values = [[name, jp_name, raised_stat, lowered_stat]]
        name, _, raised, lowered = flatten_one_level(found.values)

        return cls(name.title(), raised, lowered)

    @classmethod
    def get_all(cls) -> Iterator[Nature]:
        df = pd.read_csv(ROOT / config.paths.natures)

        for _, (name, _, raised, lowered) in df.iterrows():
            yield cls(name, raised, lowered)

    def __mod__(self, other) -> float:
        """Return the modifier for this Nature on this stat."""
        if not isinstance(other, str):
            raise TypeError(
                f"unsupported operand type(s) for %: {type(self)} and {type(other)}")

        if other not in STAT_NAMES:
            raise ValueError(
                f"Nature % stat: stat must be one of {STAT_NAMES}")

        modifier = 1.0
        if self.raised == other:
            modifier += NATURE_MODIFIER
        if self.lowered == other:
            modifier -= NATURE_MODIFIER

        return modifier

    @property
    def modifiers(self) -> SixFloats:
        return tuple(self % stat for stat in STAT_NAMES)

    @property
    def is_neutral(self) -> bool:
        return (self.raised == self.lowered)

    def __str__(self) -> str:
        if self.is_neutral:
            return f"{self.name.title()} (±)"

        return f"{self.name.title()} (+{self.raised}/-{self.lowered})"


def get_characteristic(characteristic: str) -> tuple[str, int]:
    data = pd.read_csv(ROOT / config.paths.characteristics)
    (_, high_stat, modulo), * \
        _ = data.loc[data.Characteristic.str.lower() ==
                     characteristic.lower()].values
    return high_stat, modulo


def get_all_characteristics() -> tuple[str]:
    """ Return the names of all characteristics. """
    data = pd.read_csv(ROOT / config.paths.characteristics)

    return tuple(sorted(data.Characteristic))


def calculate_stat(level: int, base: int, iv: int, ev: int, nature: float, *, hp: bool = False) -> int:
    """ Give the value of the statistic using the given values. """
    x = ((2 * base + iv + ev // 4) * level) // 100
    return x + level + 10 if hp else int((x + 5) * nature)


class HiddenPowerType(Enum):
    FIGHTING = 0
    FLYING = 1
    POISON = 2
    GROUND = 3
    ROCK = 4
    BUG = 5
    GHOST = 6
    STEEL = 7
    FIRE = 8
    WATER = 9
    GRASS = 10
    ELECTRIC = 11
    PSYCHIC = 12
    ICE = 13
    DRAGON = 14
    DARK = 15


def get_hp_type(*ivs: int) -> HiddenPowerType:
    """ Calculate the Hidden Power type from the given IVs (HP, Atk, Def, SpA, SpD, Spe). """

    # The Hidden Power algorithm uses the IVs in a different order:
    # HP, Atk, Def, Spe, SpA, SpD
    ivs = [*ivs[:3], ivs[5], *ivs[3:5]]

    n = sum((iv & 1) << i for i, iv in enumerate(ivs))
    return HiddenPowerType(n * 15 // 63)
