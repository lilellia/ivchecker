from functools import partial
import itertools

from ivchecker.engine import Characteristic, HPType, Nature, Stat, calculate_stat, get_basestats
from ivchecker.utils import SixInts


def check_ivs(
    pokemon: str,
    generation: int,
    level: int,
    actual_stats: SixInts,
    nature_name: str,
    evs: SixInts,
    characteristic: Characteristic | None,
    hidden_power_type: str
) -> tuple[list[int]]:
    """ Get the possible IVs for a Pokémon. """
    options: dict[Stat, list[int]] = {}

    # 1: Get the Pokémon's base stats
    basestats = get_basestats(pokemon=pokemon, generation=generation)

    # 2: Filter by actual stats
    nature = Nature.from_name(nature_name)
    for base, actual, ev, stat in zip(basestats, actual_stats, evs, Stat):
        options[stat] = [iv for iv in range(32) if actual == calculate_stat(level, base, iv, ev, nature % stat, stat)]

    # 3: Filter by characteristic
    if all(options.values()) and characteristic:
        # The characteristic determines the residue mod 5
        options[characteristic.high_stat] = [
            iv for iv in options[characteristic.high_stat]
            if iv % 5 == characteristic.residue
        ]

        # And we also know that no other IV can exceed this one.
        if not options:
            raise ValueError(f"No possible IVs found. Check entered stats for errors.")
        cap = max(options[characteristic.high_stat])
        for stat, opts in options.items():
            options[stat] = [iv for iv in opts if iv <= cap]

    # 4: Filter by hidden power type.
    # To speed up calculation, observe that HP calculations only require
    # the least significant bit, so we'll do our initial filtering in ℤ/2.
    if all(options.values()) and hidden_power_type:
        lsb = {stat: set(x & 1 for x in opts)
               for stat, opts in options.items()}
        bit_options: dict[Stat, set[int]] = {stat: set() for stat in Stat}

        for ivs in itertools.product(*lsb.values()):
            if HPType.get(*ivs).name.lower() == hidden_power_type.lower():
                # we have a match, so add these IVs to the set
                for stat, iv in zip(Stat, ivs):
                    bit_options[stat].add(iv)

        # With the bit matches resolved, we just need to filter the
        # actual IV possibilities.
        for stat, opts in options.items():
            options[stat] = [iv for iv in opts if iv & 1 in bit_options[stat]]

    # Filtering done, so we just return the results.
    return tuple(options[stat] for stat in Stat)


def get_ranges(pokemon: str, generation: int, level: int) -> tuple[tuple[int, int, int]]:
    basestats = get_basestats(pokemon=pokemon, generation=generation)

    output: dict[Stat, tuple[int, int, int]] = {}

    for stat, base in zip(Stat, basestats):
        f = partial(calculate_stat, level=level, base=base, stat=stat)

        min_nature, max_nature = (1, 1) if stat == Stat.HP else (0.9, 1.1)
        minimum = f(iv=0, ev=0, nature=min_nature)
        maximum_0 = f(iv=31, ev=0, nature=max_nature)
        maximum_252 = f(iv=31, ev=252, nature=max_nature)

        output[stat] = (minimum, maximum_0, maximum_252)

    return tuple(output[stat] for stat in Stat)
