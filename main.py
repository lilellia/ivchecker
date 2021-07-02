import argparse
import csv
import decimal
import itertools
import json
import pathlib


# path to this folder
HERE = pathlib.Path(__file__).parent


# read static data from files
with open(HERE / 'natures.csv') as f:
    reader = csv.reader(f)
    next(reader)
    NATURES = list(reader)

with open(HERE / 'basestats.csv') as f:
    reader = csv.reader(f)
    next(reader)
    BASE_STATS = list(reader)

with open(HERE / 'characteristics.json') as f:
    CHARACTERISTICS = json.load(f)

HP_LOOKUP = [
        'Fighting', 'Flying', 'Poison', 'Ground', 'Rock', 'Bug', 'Ghost', 'Steel', 'Fire',
        'Water', 'Grass', 'Electric', 'Psychic', 'Ice', 'Dragon', 'Dark'
]

def nature(name: str) -> tuple:
    """ Convert the name of a nature to stat modifiers (HP, ATK, DEF, SPA, SPD, SPE).
    
    Each element of the resulting tuple is a decimal.Decimal object.
    The first element (HP) is always 1 (since no nature modifies HP).
    """
    for _, en, jp, hp, atk, def_, spa, spd, spe, *_ in NATURES:
        if name.title() in (en, jp):
            # if the EN or JP name matches, use that row.
            return tuple(decimal.Decimal(x) for x in (hp, atk, def_, spa, spd, spe))

    raise argparse.ArgumentError(f'Invalid nature: {name}')

def pokemon(name: str) -> tuple:
    """ Convert the name of a Pokeḿon to a tuple of its base stats. """
    for pkmn, *base_stats in BASE_STATS:
        if pkmn == name.lower():
            return tuple(int(x) for x in base_stats)

    raise argparse.ArgumentError(f'Invalid Pokémon: {name}')

def characteristic(s: str) -> tuple:
    """ Convert a characteristic to a tuple of (stat, modulo) """
    try:
        res = CHARACTERISTICS[s.capitalize()]
        return res['stat'], res['modulo']
    except KeyError:
        raise argparse.ArgumentError(f'Invalid characteristic: {s}')


def calculate_stat(level: int, base: int, iv: int, ev: int, nature: float, *, hp: bool = False) -> int:
    """ Give the value of the statistic using the given values. """
    x = ((2 * base + iv + ev // 4) * level) // 100
    return x + level + 10 if hp else int((x + 5) * nature)


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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('pokemon', type=pokemon)
    parser.add_argument('-s', '--stats', type=int, nargs=6, required=True)
    parser.add_argument('-l', '--level', type=int, required=True)
    parser.add_argument('-n', '--nature', type=nature, required=True)
    parser.add_argument('-e', '--evs', type=int, default=[0, 0, 0, 0, 0, 0], nargs=6)
    parser.add_argument('-g', '--gen', '--generation', type=int, default=8)
    parser.add_argument('-c', '--char', '--characteristic', dest='characteristic', type=characteristic)
    args = parser.parse_args()

    stat_names = ['HP', 'Atk', 'Def', 'SpA', 'SpD', 'Spe']
    options = dict.fromkeys(stat_names)

    # stage 1: filter by stats
    for base, given, ev, nature_mod, stat in zip(args.pokemon, args.stats, args.evs, args.nature, stat_names):
        options[stat] = [iv for iv in range(32)
            if calculate_stat(level=args.level, base=base, iv=iv, ev=ev, nature=nature_mod, hp=(stat=='HP')) == given
        ]

    # stage 2: filter by characteristic
    if args.characteristic:
        # use the modulo result to filter the corresponding stat
        stat, mod = args.characteristic
        options[stat] = [iv for iv in options[stat] if iv % 5 == mod]

        # and we also know that no other IV can exceed this one
        cap = max(options[stat])
        for other_stat in stat_names:
            if stat == other_stat:
                continue
            options[other_stat] = [iv for iv in options[other_stat] if iv <= cap]

    for stat, opt in options.items():
        print(f'{stat:>3s} {opt or "ERROR!"}')


if __name__ == '__main__':
    main()