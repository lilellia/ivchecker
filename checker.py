import argparse
import decimal
import itertools

import utils


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('pokemon', type=utils.pokemon)
    parser.add_argument('-s', '--stats', type=int, nargs=6, required=True)
    parser.add_argument('-l', '--level', type=int, required=True)
    parser.add_argument('-n', '--nature', type=utils.nature, required=True)
    parser.add_argument('-e', '--evs', type=int, default=[0, 0, 0, 0, 0, 0], nargs=6)
    parser.add_argument('-g', '--gen', '--generation', type=int, default=8)
    parser.add_argument('-c', '--char', '--characteristic', type=utils.characteristic)
    parser.add_argument('-hp', '--hidden-power')
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()

    stat_names = ['HP', 'Atk', 'Def', 'SpA', 'SpD', 'Spe']
    options = dict.fromkeys(stat_names)

    # stage 0: update base stats according to generation
    name, *stats = args.pokemon
    args.pokemon = [name] + utils.update_base_stats(name, stats, gen=args.gen)

    if args.verbose:
        print(args.pokemon[0].title(), end=', ')
        if all(x == 1 for x in args.nature):
            print('neutral nature')
        else:
            plus = args.nature.index(decimal.Decimal('1.1'))
            minus = args.nature.index(decimal.Decimal('0.9'))
            print(f'nature = +{stat_names[plus]}/-{stat_names[minus]}')

    # stage 1: filter by stats
    for base, given, ev, nature_mod, stat in zip(args.pokemon[1:], args.stats, args.evs, args.nature, stat_names):
        options[stat] = [iv for iv in range(32)
            if utils.calculate_stat(level=args.level, base=base, iv=iv, ev=ev, nature=nature_mod, hp=(stat=='HP')) == given
        ]

    # stage 2: filter by characteristic (as long as there are no errors)
    if args.char and all(options.values()):
        # use the modulo result to filter the corresponding stat
        stat, mod = args.char
        options[stat] = [iv for iv in options[stat] if iv % 5 == mod]

        # and we also know that no other IV can exceed this one
        cap = max(options[stat])
        for other_stat in stat_names:
            if stat == other_stat:
                continue
            options[other_stat] = [iv for iv in options[other_stat] if iv <= cap]

    # stage 3: filter by hidden power type (as long as their were no errors)
    # to speed up computation, we observe that the HP type calculations only require the least signifant bit,
    # so we'll reduce our options mod 2
    if args.hidden_power and all(options.values()):
        lsb = {k: set(a % 2 for a in v) for k, v in options.items()}

        bit_options = {s: set() for s in stat_names}
        for ivs in itertools.product(*lsb.values()):
            if utils.hidden_power(*ivs)[0] == args.hidden_power.capitalize():
                for s, i in zip(stat_names, ivs):
                    bit_options[s].add(i)

        for k in stat_names:
            options[k] = [iv for iv in options[k] if iv % 2 in bit_options[k]]

    # output possible IVs
    for base, (stat, opt) in zip(args.pokemon[1:], options.items()):
        b = f' [Base: {base:>3}]' if args.verbose else ''   # handle base stats if verbose output is requested

        # handle groupings (0 options -> error, 1 option -> itself, more than that -> range)
        if len(opt) == 0:
            ivs = 'ERROR'
        elif len(opt) == 1:
            ivs = opt[0]
        else:
            ivs = f'{min(opt)}-{max(opt)}'
            if all(i % 2 == 0 for i in opt):
                ivs += ' (even)'
            elif all(i % 2 == 1 for i in opt):
                ivs += ' (odd)'

        # and actually do the printing
        print(f'{stat:>3s}{b} - IVs: {ivs}')


if __name__ == '__main__':
    main()