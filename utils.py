from contextlib import suppress
from enum import Enum
# import fuzzywuzzy.process
import json
from pathlib import Path
import pandas as pd
import sys
import yaml


# path to this folder
HERE = Path(__file__).parent.resolve()

# configuration object
from configuration import Config
config = Config.from_yaml(HERE / "config.yaml")

# helper type alias
SixInts = tuple[int, int, int, int, int, int]
SixFloats = tuple[float, float, float, float, float, float]


def _get_modern_basestats(pokemon: str) -> SixInts:
    """ Get the most recent basestats for the given Pokémon. """
    data = pd.read_csv(HERE / config.paths.basestats)
    filtered = data[data.Name.str.lower() == pokemon.lower()]

    if filtered.empty:
        # could not find the pokemon
        raise ValueError(f"Could not find base stats for {pokemon!r}")

    _, *stats = filtered.values[0]  # bs.values = [[name, HP, Atk, Def, SpA, SpD, Spe]]
    return tuple(stats)


def _get_stat_changes(pokemon: str) -> dict[int, SixInts]:
    """ Get all known stat changes for the given Pokémon, by generation. """
    data = pd.read_csv(HERE / config.paths.statchanges)
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


def get_nature(nature: str) -> SixFloats:
    natures = pd.read_csv(HERE / config.paths.natures)
    n = natures[natures.Name.str.lower() == nature.lower()]

    if n.empty:
        # could not find the nature
        raise ValueError(f"Could not find nature {nature!r}")

    # n.values = [[name, jpname, hp, atk, def, spa, spd, spe, liked flavor, disliked flavor]]
    _, _, *mods, _, _ = n.values[0]
    return tuple(mods)


def get_all_natures() -> tuple[str]:
    """ Return the names of all natures. """
    natures = pd.read_csv(HERE / config.paths.natures)
    return tuple(sorted(natures.Name))


def get_characteristic(characteristic: str) -> tuple[str, int]:
    data = pd.read_csv(HERE / config.paths.characteristics)
    (_, high_stat, modulo), *_ = data.loc[data.Characteristic.str.lower() == characteristic.lower()].values
    return high_stat, modulo

def get_all_characteristics() -> tuple[str]:
    """ Return the names of all characteristics. """
    data = pd.read_csv(HERE / config.paths.characteristics)

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
    ivs = ivs[:3], ivs[5], ivs[3:5]

    n = sum((iv & 1) << i for i, iv in enumerate(ivs))
    return HiddenPowerType(n * 15 // 63)