from __future__ import annotations
from contextlib import suppress
from dataclasses import dataclass
from enum import Enum
import pandas as pd
from typing import Iterator

from ivchecker.utils import ROOT, config, fuzzy, search_dataframe

class Stat(Enum):
    HP = "HP"
    ATK = "Atk"
    DEF = "Def"
    SPA = "SpA"
    SPD = "SpD"
    SPE = "Spe"
    
    @classmethod
    def names(cls) -> list[str]:        
        return [stat.value for stat in cls]
    

@dataclass
class Nature:
    name: str
    raised: Stat
    lowered: Stat
    
    @classmethod
    def from_name(cls, name: str) -> Nature:
        df = pd.read_csv(ROOT / config.paths.natures)
        name, _, raised, lowered = search_dataframe(df, "Name", name)
        raised = Stat[raised.upper()]
        lowered = Stat[lowered.upper()]
        
        return cls(name.title(), raised, lowered)
    
    @classmethod
    def read_all(cls) -> Iterator[Nature]:
        df = pd.read_csv(ROOT / config.paths.natures)
        
        for _, (name, _, raised, lowered) in df.iterrows():
            raised = Stat[raised.upper()]
            lowered = Stat[lowered.upper()]
            
            yield cls(name, raised, lowered)
    
    def __mod__(self, stat: Stat) -> float:
        """Return the modifier for this Nature on the given stat."""      
        modifier = 1.0
        if self.raised == stat: modifier += 0.1
        if self.lowered == stat: modifier -= 0.1
        
        return modifier
    
    @property
    def modifiers(self) -> tuple[float, float, float, float, float, float]:
        return tuple(self % stat for stat in Stat)
    
    @property
    def is_neutral(self) -> bool:
        return (self.raised == self.lowered)
    
    def __str__(self) -> str:
        if self.is_neutral:
            return f"{self.name.title()} (±)"
        
        return f"{self.name.title()} (+{self.raised.value}/-{self.lowered.value})"
    

@dataclass
class Characteristic:
    description: str
    high_stat: Stat
    residue: int
    
    @classmethod
    def read_all(cls) -> Iterator[str]:
        df = pd.read_csv(ROOT / config.paths.characteristics)
        yield from df["Characteristic"]
        
    @classmethod
    def get(cls, characteristic: str) -> Characteristic:
        df = pd.read_csv(ROOT / config.paths.characteristics)
        _, high, residue = search_dataframe(df, "Characteristic", characteristic)
        
        return cls(characteristic, Stat[high.upper()], residue)
    

class HPType(Enum):
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
    
    @classmethod
    def get(cls, hp: int, atk: int, def_: int, spa: int, spd: int, spe: int) -> HPType:
        """Calculate the HP type based on the given IVs."""
        # the HP algorithm uses the stats in a different order
        ivs = hp, atk, def_, spe, spa, spd
        
        n = sum((iv & 1) << i for i, iv in enumerate(ivs))
        return cls(n * 15 // 63)
    

def get_all_pokemon_names() -> list[str]:
    df = pd.read_csv(ROOT / config.paths.basestats)
    return df["Name"].tolist()


def _get_modern_basestats(pokemon: str) -> tuple[int, int, int, int, int, int]:
    """Get the most recent basestats for the given Pokémon."""
    df = pd.read_csv(ROOT / config.paths.basestats)
    
    try:
        _, *stats = search_dataframe(df, "Name", pokemon)
        return tuple(stats)
    except ValueError:
        opt1, opt2 = fuzzy(pokemon, options=get_all_pokemon_names(), limit=2)
        raise ValueError(f"Could not find Pokémon {pokemon}.\nDid you mean {opt1} or {opt2}?")


def _get_stat_changes(pokemon: str) -> dict[int, tuple[int, int, int, int, int, int]]:
    """Get all known stat changes for the given Pokémon, by generation."""
    df = pd.read_csv(ROOT / config.paths.basestats)
    filtered = df[df["Pokemon"].str.lower() == pokemon.lower()]
    
    return {gen: tuple(stats) for _, _, gen, *stats in filtered.values}
    
def get_basestats(pokemon: str, generation: int) -> tuple[int, int, int, int, int, int]:
    """Return the basestats for the given Pokémon in the given generation."""
    modern_stats = _get_modern_basestats(pokemon)
    
    if generation == config.generations.most_recent:
        # we're good to just return these stats
        return modern_stats
    
    changes = _get_stat_changes(pokemon)
    if not changes:
        # This Pokémon doesn't have any stat changes, so
        # we can just return the modern stats as well.
        return modern_stats
    
    # Otherwise, there are changes that we need to undo.
    for g in range(config.generations.most_recent, generation - 1, -1):
        with suppress(KeyError):
            return changes[g]
        
    # the stat changes were long enough ago that they don't affect us
    return modern_stats


def calculate_stat(level: int, base: int, iv: int, ev: int, nature: float, stat: Stat) -> int:
    """Give the value of the statistic using the given values."""
    
    result = (2 * base + iv + (ev // 4)) * level // 100
    
    if stat == Stat.HP:
        return result + level + 10
    
    return int((result + 5) * nature)
    