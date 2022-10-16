from argparse import Namespace
import itertools
import json
from pathlib import Path

from gui import Button, Dropdown, EditableWidget, Frame, Label, Textbox, TabbedDisplay, Theme, Window
import utils

__version__ = '2.0β'

STAT_NAMES = ("HP", "Atk", "Def", "SpA", "SpD", "Spe")

def check(args: Namespace):
    stat_names = ('HP', 'Atk', 'Def', 'SpA', 'SpD', 'Spe')
    options = dict.fromkeys(stat_names)

    # step 1: get the Pokémon's base stats
    basestats = utils.get_basestats(pokemon=args.pokemon, gen=args.generation)
    
    # step 2: filter possible IVs by stats
    nature = utils.get_nature(args.nature)
    for base, actual, ev, nature_mod, stat_name in zip(basestats, args.stats, args.evs, nature, STAT_NAMES):
        options[stat_name] = [
            iv for iv in range(32)
            if actual == utils.calculate_stat(args.level, base, iv, ev, nature_mod, hp=(stat_name=="HP"))
        ]

    # step 2: filter by characteristic (as long as there were no errors)
    if args.characteristic and all(options.values()):
        # use the modulo result to filter the corresponding stat
        char_stat, residue = utils.get_characteristic(args.characteristic)
        options[char_stat] = [iv for iv in options[char_stat] if iv % 5 == residue]

        # then we also know that no other IV can exceed this one
        cap = max(options[char_stat])
        for stat_name in stat_names:
            options[stat_name] = [iv for iv in options[stat_name] if iv <= cap]

    # step 3: filter by hidden power type (as long as there were no errors)
    # To speed up calculation, we observe that the HP type calculations only require the least significant bit,
    # so we'll do all our initial filtering in Z/2.
    if args.hidden_power_type and all(options.values()):
        lsb = {stat_name: set(a % 2 for a in poss) for stat_name, poss in options.items()}
        bit_options = {s: set() for s in stat_names}
    
        for ivs in itertools.product(*lsb.values()):
            if utils.calc_hp_type(*ivs).name.lower() == args.hidden_power_type.lower():
                # we have a match, so add these IVs to the set
                for s, i in zip(stat_names, ivs):
                    bit_options[s].add(i)

        # with the bit matches resolved, we just need to filter the actual IV possibilities
        for stat_name in stat_names:
            options[stat_name] = [iv for iv in options[stat_name] if iv % 2 in bit_options[stat_name]]

    # with filtering done, we can output our results
    output: list[str] = []
    for stat_name, ivs in options.items():
        # handle groupings (0 options → error, 1 option → itself, 2+ options → range)
        if len(ivs) == 0:
            output.append("ERROR")
        elif len(ivs) == 1:
            output.append(ivs[0])
        else:
            s = f'{min(ivs)}-{max(ivs)}'

            # this additional parity comment is only applicable when hidden power testing as well
            if all(i % 2 == 0 for i in ivs):
                s += ' (even)'
            elif all(i % 2 == 1 for i in ivs):
                s += ' (odd)'
            output.append(s)

    # write output
    for stat, ivs in zip(STAT_NAMES, output):
        args.ui[f"ivs_{stat}"].contents = ivs
    return output


# def get_ranges(args: argparse.Namespace):
#     # stage 0: update base stats according to generation
#     pkmn, *gen8_stats = args.pokemon
#     args.pokemon[1:] = utils.update_base_stats(pkmn, gen8_stats, gen=args.gen)

#     stat_names = ('HP', 'Atk', 'Def', 'SpA', 'SpD', 'Spe')

#     # calculate min/max stats
#     output = [
#         [
#             '---', 0,
#             *[
#                 utils.calculate_stat(args.level, base, iv=0, ev=0, nature=0.9, hp=(stat_name=='HP'))
#                 for base, stat_name in zip(args.pokemon[1:], stat_names)
#             ]
#         ],

#         [
#             'neutral', 0,
#             *[
#                 utils.calculate_stat(args.level, base, iv=0, ev=0, nature=1, hp=(stat_name=='HP'))
#                 for base, stat_name in zip(args.pokemon[1:], stat_names)
#             ]
#         ],

#         [
#             'neutral', 31,
#             *[
#                 utils.calculate_stat(args.level, base, iv=31, ev=0, nature=1, hp=(stat_name=='HP'))
#                 for base, stat_name in zip(args.pokemon[1:], stat_names)
#             ]
#         ],

#         [
#             '+++', 31,
#             *[
#                 utils.calculate_stat(args.level, base, iv=31, ev=0, nature=1.1, hp=(stat_name=='HP'))
#                 for base, stat_name in zip(args.pokemon[1:], stat_names)
#             ]
#         ]
#     ]

#     print(tabulate.tabulate(output, headers=['Nature', 'IV', *stat_names], tablefmt='fancy_grid'))
#     return output


# def show_base(args: argparse.Namespace):
#     # stage 0: update base stats according to generation
#     pkmn, *gen8_stats = args.pokemon
#     args.pokemon[1:] = utils.update_base_stats(pkmn, gen8_stats, gen=args.gen)

#     print(tabulate.tabulate(
#         [[pkmn.title(), *args.pokemon[1:]]],
#         headers=['', 'HP', 'Atk', 'Def', 'SpA', 'SpD', 'Spe'],
#         tablefmt='fancy_grid'
#     ))
    


# def main():
#     parser = argparse.ArgumentParser()
#     parser.add_argument('pokemon', type=utils.pokemon, help='the name of the Pokémon')
#     parser.add_argument('-g', '--gen', '--generation', type=int, default=8, help="the game's generation number (default=8)")
#     parser.add_argument('-v', '--verbose', action='store_true')
#     parser.add_argument('--version', action='version', version=f'%(prog)s v{__version__}')

#     subparsers = parser.add_subparsers(title='valid subcommands', required=True)

#     # subparser for IV checker -----------------------------------------------------------------
#     checker = subparsers.add_parser('check', help="determine a Pokémon's IVs")
#     checker.add_argument(
#         '-s', '--stats',
#         type=int, nargs=6, required=True,
#         help='the current stats for the Pokémon, given as -s HP ATK DEF SPA SPD SPE'
#     )
#     checker.add_argument(
#         '-l', '--level',
#         type=int, required=True,
#         help='the current level of the Pokémon'
#     )
#     checker.add_argument(
#         '-n', '--nature',
#         type=utils.nature, required=True,
#         help='the nature of the Pokémon, e.g., "adamant"'
#     )
#     checker.add_argument(
#         '-c', '--char', '--characteristic',
#         type=utils.characteristic, required=False,
#         help="the Pokémon's characteristic (e.g., \"capable of taking hits\"), optional"
#     )
#     checker.add_argument(
#         '-hp', '--hidden-power',
#         type=utils.type_, required=False,
#         help="the Pokémon's Hidden Power type (e.g., \"water\"), optional"
#     )
#     checker.add_argument(
#         '-e', '--evs',
#         type=int, nargs=6, required=False, default=[0, 0, 0, 0, 0, 0],
#         help="the number of EVs the Pokémon has in each stat, given as -e HP ATK DEF SPA SPD SPE. (All = 0 when this flag is not passed.)"
#     )
#     checker.set_defaults(func=check)

#     # subparser for possible ranges -----------------------------------------------------------------
#     ranges = subparsers.add_parser('ranges', help='determine ranges of possible stats')
#     ranges.add_argument(
#         '-l', '--level',
#         type=int, required=True,
#         help='the current level of the Pokémon'
#     )
#     ranges.set_defaults(func=get_ranges)

#     # subparser for base stats -----------------------------------------------------------------
#     showbase = subparsers.add_parser('base', help='show base stats')
#     showbase.set_defaults(func=show_base)

#     args = parser.parse_args()
#     args.func(args)

def initialize_check_tab(frame: Frame) -> None:
    frame.form: dict[str, EditableWidget] = dict()

    Label(master=frame, text="Generation*", anchor="e").grid(0, 0, opad=(5, 0))
    generation_options = ("8・VIII", "7・VII", "6・VI", "5・V", "4・IV", "3・III")
    frame.form["generation"] = Dropdown(master=frame, options=generation_options).grid(0, 1, columnspan=2)

    Label(master=frame, text="Pokémon*", anchor="e").grid(1, 0, opad=(5, 0))
    frame.form["pokémon"] = Textbox(master=frame).grid(1, 1, columnspan=6)

    Label(master=frame, text="Level*", anchor="e").grid(2, 0, opad=(5, 0))
    frame.form["level"] = Textbox(master=frame).grid(2, 1, columnspan=6)

    Label(master=frame, text="Stats*", anchor="e").grid(4, 0, opad=(5, 0))
    for j, stat in enumerate(STAT_NAMES, start=1):
        Label(master=frame, text=stat, anchor="center").grid(row=3, column=j)
        frame.form[f"stat_{stat}"] = Textbox(master=frame).config(width=4).grid(row=4, column=j)

    Label(master=frame, text="EVs", anchor="e").grid(5, 0, opad=(5, 0))
    for j, stat in enumerate(STAT_NAMES, start=1):
        frame.form[f"evs_{stat}"] = Textbox(master=frame).config(width=4).grid(row=5, column=j)
        frame.form[f"evs_{stat}"].contents = "0"  # set default value of 0

    Label(master=frame, text="Nature*", anchor="center").grid(6, 1, columnspan=2, opad=(0, 5))
    natures = ("",) + utils.get_all_natures()
    frame.form["nature"] = Dropdown(master=frame, options=natures).grid(7, 1, columnspan=2)
    

    Label(master=frame, text="Characteristic", anchor="center").grid(6, 3, columnspan=2, opad=(0, 5))
    characteristics = ("",) + utils.get_all_characteristics()
    frame.form["characteristic"] = Dropdown(master=frame, options=characteristics).grid(7, 3, columnspan=2)

    Label(master=frame, text="HP Type", anchor="center").grid(6, 5, columnspan=2, opad=(0, 5))
    types = ("",) + tuple(sorted(t.name.title() for t in utils.HiddenPowerType))
    frame.form["hidden-power-type"] = Dropdown(master=frame, options=types).grid(7, 5, columnspan=2)

    Label(master=frame, text="IVs", anchor="e").grid(11, 0, opad=(5, 0))
    for j, stat in enumerate(STAT_NAMES, start=1):
        Label(master=frame, text=stat, anchor="center").grid(row=10, column=j)
        frame.form[f"ivs_{stat}"] = Textbox(master=frame).config(width=12).grid(row=11, column=j)

    def check_button_callback():
        ui: dict[str, EditableWidget] = frame.form

        # clear the IV fields
        for key, widget in ui.items():
            if key.startswith("ivs_"):
                widget.clear()

        # read generation from dropdown, converting, e.g. "4・IV" -> 4
        gen: int = int(ui["generation"].contents.split("・")[0])

        args = Namespace(
            ui=ui,  # passed so that check() can output back to the ui
            generation=gen,
            pokemon=ui["pokémon"].contents,
            level=int(ui["level"].contents),
            stats=[int(ui[f"stat_{stat}"].contents) for stat in STAT_NAMES],
            evs=[int(ui[f"evs_{stat}"].contents) for stat in STAT_NAMES],
            nature=ui["nature"].contents,
            characteristic=ui["characteristic"].contents,
            hidden_power_type=ui["hidden-power-type"].contents
        )
        check(args)

    Button(master=frame, text="Calculate IVs", callback=check_button_callback).grid(9, 1, columnspan=6, opad=(0, 20))


def initialize_ranges_tab(frame: Frame) -> None:
    pass


def initialize_basestat_tab(frame: Frame) -> None:
    pass



def main():
    # get configs
    with open(Path(__file__).resolve().parent / "themes.json") as f:
        theme_data = json.load(f)
    active_theme = theme_data["active_theme"]  # get name of active theme
    theme = Theme(**theme_data["themes"][active_theme])  # load data for that theme

    window = Window(size=(730, 350), title=f"Pokémon IV Checker v{__version__}")
    
    # activate the theme
    # This must occur after a Tk object (i.e., `window`) is initialized.
    theme.use()

    # Create the tab display and its tabs.
    tabs = TabbedDisplay(master=window)
    tabs.pack(expand=True, fill="both")
    check_tab, ranges_tab, basestat_tab = tabs.add_tabs("Check IVs", "Show Ranges", "Show Base Stats")

    # Initialize the tabs individually.
    initialize_check_tab(check_tab)
    initialize_ranges_tab(ranges_tab)
    initialize_basestat_tab(basestat_tab)

    # Actually run the application
    window.run()


if __name__ == '__main__':
    main()