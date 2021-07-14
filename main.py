import argparse
import decimal
import itertools
import tabulate

import utils


__version__ = '1.1'


def check(args: argparse.Namespace):
    stat_names = ('HP', 'Atk', 'Def', 'SpA', 'SpD', 'Spe')
    options = dict.fromkeys(stat_names)

    # stage 0: update base stats according to generation
    pkmn, *gen8_stats = args.pokemon
    args.pokemon[1:] = utils.update_base_stats(pkmn, gen8_stats, gen=args.gen)

    # step 1: filter possible IVs by stats
    for base, actual, ev, nature_mod, stat_name in zip(args.pokemon[1:], args.stats, args.evs, args.nature, stat_names):
        options[stat_name] = [
            iv for iv in range(32)
            if actual == utils.calculate_stat(args.level, base, iv, ev, nature_mod, hp=(stat_name=='HP'))
        ]

    # step 2: filter by characteristic (as long as there were no errors)
    if args.char and all(options.values()):
        # use the modulo result to filter the corresponding stat
        char_stat, residue = args.char
        options[char_stat] = [iv for iv in options[char_stat] if iv % 5 == residue]

        # then we also know that no other IV can exceed this one
        cap = max(options[char_stat])
        for stat_name in stat_names:
            options[stat_name] = [iv for iv in options[stat_name] if iv <= cap]

    # step 3: filter by hidden power type (as long as there were no errors)
    # To speed up calculation, we observe that the HP type calculations only require the least significant bit,
    # so we'll do all our initial filtering in Z/2.
    if args.hidden_power and all(options.values()):
        lsb = {stat_name: set(a % 2 for a in poss) for stat_name, poss in options.items()}
        bit_options = {s: set() for s in stat_names}
    
        for ivs in itertools.product(*lsb.values()):
            if utils.hidden_power(*ivs)[0] == args.hidden_power:
                # we have a match, so add these IVs to the set
                for s, i in zip(stat_names, ivs):
                    bit_options[s].add(i)

        # with the bit matches resolved, we just need to filter the actual IV possibilities
        for stat_name in stat_names:
            options[stat_name] = [iv for iv in options[stat_name] if iv % 2 in bit_options[stat_name]]

    # with filtering done, we can output our results
    output = []

    # output base stats and nature values
    if args.verbose:
        symb = {decimal.Decimal('1.1'): '+++', decimal.Decimal('0.9'): '---'}
        output.append(['Nature'] + [symb.get(n, '') for n in args.nature])

        output.append(['Base'] + args.pokemon[1:])

    # output IV ranges
    output.append(['IVs'])
    for stat_name, ivs in options.items():
        # handle groupings (0 options → error, 1 option → itself, 2+ options → range)
        if len(ivs) == 0:
            output[-1].append('ERROR')
        elif len(ivs) == 1:
            output[-1].append(ivs[0])
        else:
            s = f'{min(ivs)}-{max(ivs)}'

            # this additional parity comment is only applicable when hidden power testing as well
            if all(i % 2 == 0 for i in ivs):
                s += ' (even)'
            elif all(i % 2 == 1 for i in ivs):
                s += ' (odd)'
            output[-1].append(s)

    print(tabulate.tabulate(output, headers=['', *stat_names], tablefmt='fancy_grid'))
    return options


def get_ranges(args: argparse.Namespace):
    # stage 0: update base stats according to generation
    pkmn, *gen8_stats = args.pokemon
    args.pokemon[1:] = utils.update_base_stats(pkmn, gen8_stats, gen=args.gen)

    stat_names = ('HP', 'Atk', 'Def', 'SpA', 'SpD', 'Spe')

    # calculate min/max stats
    output = [
        [
            '---', 0,
            *[
                utils.calculate_stat(args.level, base, iv=0, ev=0, nature=0.9, hp=(stat_name=='HP'))
                for base, stat_name in zip(args.pokemon[1:], stat_names)
            ]
        ],

        [
            'neutral', 0,
            *[
                utils.calculate_stat(args.level, base, iv=0, ev=0, nature=1, hp=(stat_name=='HP'))
                for base, stat_name in zip(args.pokemon[1:], stat_names)
            ]
        ],

        [
            'neutral', 31,
            *[
                utils.calculate_stat(args.level, base, iv=31, ev=0, nature=1, hp=(stat_name=='HP'))
                for base, stat_name in zip(args.pokemon[1:], stat_names)
            ]
        ],

        [
            '+++', 31,
            *[
                utils.calculate_stat(args.level, base, iv=31, ev=0, nature=1.1, hp=(stat_name=='HP'))
                for base, stat_name in zip(args.pokemon[1:], stat_names)
            ]
        ]
    ]

    print(tabulate.tabulate(output, headers=['Nature', 'IV', *stat_names], tablefmt='fancy_grid'))
    return output


def show_base(args: argparse.Namespace):
    # stage 0: update base stats according to generation
    pkmn, *gen8_stats = args.pokemon
    args.pokemon[1:] = utils.update_base_stats(pkmn, gen8_stats, gen=args.gen)

    print(tabulate.tabulate(
        [[pkmn.title(), *args.pokemon[1:]]],
        headers=['', 'HP', 'Atk', 'Def', 'SpA', 'SpD', 'Spe'],
        tablefmt='fancy_grid'
    ))
    


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('pokemon', type=utils.pokemon, help='the name of the Pokémon')
    parser.add_argument('-g', '--gen', '--generation', type=int, default=8, help="the game's generation number (default=8)")
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('--version', action='version', version=f'%(prog)s v{__version__}')

    subparsers = parser.add_subparsers(title='valid subcommands', required=True)

    # subparser for IV checker -----------------------------------------------------------------
    checker = subparsers.add_parser('check', help="determine a Pokémon's IVs")
    checker.add_argument(
        '-s', '--stats',
        type=int, nargs=6, required=True,
        help='the current stats for the Pokémon, given as -s HP ATK DEF SPA SPD SPE'
    )
    checker.add_argument(
        '-l', '--level',
        type=int, required=True,
        help='the current level of the Pokémon'
    )
    checker.add_argument(
        '-n', '--nature',
        type=utils.nature, required=True,
        help='the nature of the Pokémon, e.g., "adamant"'
    )
    checker.add_argument(
        '-c', '--char', '--characteristic',
        type=utils.characteristic, required=False,
        help="the Pokémon's characteristic (e.g., \"capable of taking hits\"), optional"
    )
    checker.add_argument(
        '-hp', '--hidden-power',
        type=utils.type_, required=False,
        help="the Pokémon's Hidden Power type (e.g., \"water\"), optional"
    )
    checker.add_argument(
        '-e', '--evs',
        type=int, nargs=6, required=False, default=[0, 0, 0, 0, 0, 0],
        help="the number of EVs the Pokémon has in each stat, given as -e HP ATK DEF SPA SPD SPE. (All = 0 when this flag is not passed.)"
    )
    checker.set_defaults(func=check)

    # subparser for possible ranges -----------------------------------------------------------------
    ranges = subparsers.add_parser('ranges', help='determine ranges of possible stats')
    ranges.add_argument(
        '-l', '--level',
        type=int, required=True,
        help='the current level of the Pokémon'
    )
    ranges.set_defaults(func=get_ranges)

    # subparser for base stats -----------------------------------------------------------------
    showbase = subparsers.add_parser('base', help='show base stats')
    showbase.set_defaults(func=show_base)

    args = parser.parse_args()
    args.func(args)



if __name__ == '__main__':
    main()