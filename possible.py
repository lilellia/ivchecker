import argparse
import csv
import decimal
import itertools
import json
import pathlib

import utils


# path to this folder
HERE = pathlib.Path(__file__).parent


# read static data from files
with open(HERE / 'basestats.csv', encoding='UTF-8') as f:
    reader = csv.reader(f)
    next(reader)
    BASE_STATS = list(reader)

with open(HERE / 'statchanges.json', encoding='UTF-8') as f:
    STAT_CHANGES = json.load(f)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('pokemon', type=utils.pokemon, help='the name of the Pokémon')
    parser.add_argument('level', type=int, help='the level of the Pokémon')
    parser.add_argument('-g', '--gen', '--generation', type=int, default=8, help='the generation of the game')
    parser.add_argument('-e', '--evs', action='store_const', const=252, default=0, help='allow EVs for max calculation')
    args = parser.parse_args()

    # stage 0: update base stats according to generation
    name, *stats = args.pokemon
    args.pokemon = [name] + utils.update_base_stats(name, stats, gen=args.gen)

    # calculate min/max stats
    for base, stat_name in zip(args.pokemon[1:], 'HP Atk Def SpA SpD Spe'.split()):
        minimum = utils.calculate_stat(
            level=args.level, base=base, iv=0, ev=0, nature=0.9, hp=(stat_name=='HP')
        )
        maximum = utils.calculate_stat(
            level=args.level, base=base, iv=31, ev=args.evs, nature=1.1, hp=(stat_name=='HP')
        )

        print(f'{stat_name:>3}: {minimum}-{maximum}')

if __name__ == '__main__':
    main()