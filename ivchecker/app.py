import itertools
from pathlib import Path

from .utils import STAT_NAMES, calculate_stat, get_basestats, get_characteristic, get_hp_type, get_nature, SixInts

def check_ivs(
    pokemon: str,
    generation: int,
    level: int,
    actual_stats: SixInts,
    nature_name: str,
    evs: SixInts,
    characteristic: str,
    hidden_power_type: str
) -> dict[str, list[int]]:
    """ Get the possible IVs for a Pokémon. """
    options: dict[str, list[int]] = {}

    # 1: Get the Pokémon's base stats
    basestats = get_basestats(pokemon=pokemon, generation=generation)

    # 2: Filter by actual stats
    nature = get_nature(nature_name)
    for base, actual, ev, nature_mod, stat in zip(basestats, actual_stats, evs, nature, STAT_NAMES):
        is_hp = (stat == "HP")
        options[stat] = [
            iv for iv in range(32)
            if actual == calculate_stat(level, base, iv, ev, nature_mod, hp=is_hp)
        ]

    # 3: Filter by characteristic
    if all(options.values()) and characteristic:
        highstat, residue = get_characteristic(characteristic)

        # The characteristic determines the residue mod 5
        options[highstat] = [iv for iv in options[highstat] if iv % 5 == residue]

        # And we also know that no other IV can exceed this one.
        cap = max(options[highstat])
        for stat, opts in options.items():
            options[stat] = [iv for iv in opts if iv <= cap]

    # 4: Filter by hidden power type.
    # To speed up calculation, observe that HP calculations only require
    # the least significant bit, so we'll do our initial filtering in ℤ/2.
    if all(options.values()) and hidden_power_type:
        lsb = {stat: set(x & 1 for x in opts) for stat, opts in options.items()}
        bit_options = {stat: set() for stat in STAT_NAMES}

        for ivs in itertools.product(*lsb.values()):
            if get_hp_type(*ivs).name.lower() == hidden_power_type.lower():
                # we have a match, so add these IVs to the set
                for stat, iv in zip(STAT_NAMES, ivs):
                    bit_options[stat].add(iv)
                
        # With the bit matches resolved, we just need to filter the
        # actual IV possibilities.
        for stat, opts in options.items():
            options[stat] = [iv for iv in opts if iv & 1 in bit_options[stat]]

    # Filtering done, so we just return the results.
    return tuple(options.values())