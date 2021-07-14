import csv
import decimal
import functools
import fuzzywuzzy.process
import json
import pathlib
import sys


# path to this folder
HERE = pathlib.Path(__file__).parent


# read static data from files
with open(HERE / 'natures.csv', encoding='UTF-8') as f:
    reader = csv.reader(f)
    next(reader)
    NATURES = list(reader)

with open(HERE / 'basestats.csv', encoding='UTF-8') as f:
    reader = csv.reader(f)
    next(reader)
    BASE_STATS = list(reader)

with open(HERE / 'statchanges.json', encoding='UTF-8') as f:
    STAT_CHANGES = json.load(f)

with open(HERE / 'characteristics.json', encoding='UTF-8') as f:
    CHARACTERISTICS = json.load(f)

HP_LOOKUP = [
        'Fighting', 'Flying', 'Poison', 'Ground', 'Rock', 'Bug', 'Ghost', 'Steel', 'Fire',
        'Water', 'Grass', 'Electric', 'Psychic', 'Ice', 'Dragon', 'Dark'
]


def fuzzy(matches):
    """ Provide a decorator that wraps functions to provide fuzzy text-matching warnings.
    The function should raise ValueError when the fuzzy matching should take over.
    """
    def wrapper(func):
        @functools.wraps(func)
        def wrapped(text: str):
            try:
                return func(text)
            except ValueError:
                # in this case, the input was invalid, so we'll try to fuzzy match
                (best, _), (second, _) = fuzzywuzzy.process.extract(text, matches, limit=2)
                sys.exit(f'[{func.__name__}] Could not find {text!r}. Did you mean {best!r} or {second!r}?\n')
        return wrapped
    return wrapper


@fuzzy(matches=tuple(n[1] for n in NATURES))
def nature(name: str) -> tuple:
    """ Convert the name of a nature to stat modifiers (HP, ATK, DEF, SPA, SPD, SPE).
    
    Each element of the resulting tuple is a decimal.Decimal object.
    The first element (HP) is always 1 (since no nature modifies HP).
    """
    for _, en, jp, hp, atk, def_, spa, spd, spe, *_ in NATURES:
        if name.title() in (en, jp):
            # if the EN or JP name matches, use that row.
            return tuple(decimal.Decimal(x) for x in (hp, atk, def_, spa, spd, spe))

    raise ValueError(f'Invalid nature: {name}')


@fuzzy(matches=tuple(p[0] for p in BASE_STATS))
def pokemon(name: str) -> tuple:
    """ Convert the name of a Pokeḿon to a tuple of its base stats. """
    for pkmn, *base_stats in BASE_STATS:
        if pkmn == name.lower():
            return [pkmn] + [int(x) for x in base_stats]

    raise ValueError(f'Invalid Pokémon: {name}')


@fuzzy(matches=tuple(CHARACTERISTICS.keys()))
def characteristic(s: str) -> tuple:
    """ Convert a characteristic to a tuple of (stat, modulo) """
    try:
        res = CHARACTERISTICS[s.capitalize()]
        return res['stat'], res['modulo']
    except KeyError:
        raise ValueError(f'Invalid characteristic: {s}')


def calculate_stat(level: int, base: int, iv: int, ev: int, nature: float, *, hp: bool = False) -> int:
    """ Give the value of the statistic using the given values. """
    x = ((2 * base + iv + ev // 4) * level) // 100
    return x + level + 10 if hp else int((x + 5) * nature)


@fuzzy(matches=HP_LOOKUP)
def type_(name: str):
    if name.title() in HP_LOOKUP:
        return name.title()
    raise ValueError(f'Invalid Pokémon type: {name}')


def hidden_power(hp: int, attack: int, defense: int, spattack: int, spdefense: int, speed: int) -> tuple:
    # determine type
    temp = (hp & 1) + ((attack & 1) << 1) + ((defense & 1) << 2) + ((speed & 1) << 3) + \
        ((spattack & 1) << 4) + ((spdefense & 1) << 5)
    index = temp * 15 // 63

    # determine power
    temp = bool(hp & 2) + (bool(attack & 2) << 1) + (bool(defense & 2) << 2) + (bool(speed & 2) << 3) + \
        (bool(spattack & 2) << 4) + (bool(spdefense & 2) << 5)
    power = 30 + (temp * 40 // 63)

    return (HP_LOOKUP[index], power)


def update_base_stats(pkmn, gen8_stats, gen=8):
    if gen == 8 or pkmn not in STAT_CHANGES.keys():
        # we're in current gen or there are no changes for this Pokémon
        return gen8_stats

    changes, stats = STAT_CHANGES[pkmn], None
    for g in range(5, 8):
        try:
            stats = changes[f'Gen {g}']

            if g >= gen and stats is not None:
                return stats
        except KeyError:
            pass

    return stats