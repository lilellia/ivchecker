from argparse import Namespace
from dataclasses import dataclass
from functools import partial
import itertools
import json
from pathlib import Path

from gui import Button, Dropdown, EditableWidget, Frame, Label, Textbox, TabbedDisplay, Theme, Window
import utils

__version__ = '2.0β'

# path to this folder
HERE = Path(__file__).parent

STAT_NAMES = ("HP", "Atk", "Def", "SpA", "SpD", "Spe")

@dataclass
class Config:
    active_theme: str

    @classmethod
    def from_file(cls, json_path: Path) -> "Config":
        with open(json_path) as f:
            data = json.load(f)

        return cls(**data)


def check(args: Namespace):
    options: dict[str, list[int]] = {}

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
        for stat_name in STAT_NAMES:
            options[stat_name] = [iv for iv in options[stat_name] if iv <= cap]

    # step 3: filter by hidden power type (as long as there were no errors)
    # To speed up calculation, we observe that the HP type calculations only require the least significant bit,
    # so we'll do all our initial filtering in Z/2.
    if args.hidden_power_type and all(options.values()):
        lsb = {stat_name: set(a % 2 for a in poss) for stat_name, poss in options.items()}
        bit_options = {s: set() for s in STAT_NAMES}
    
        for ivs in itertools.product(*lsb.values()):
            if utils.calc_hp_type(*ivs).name.lower() == args.hidden_power_type.lower():
                # we have a match, so add these IVs to the set
                for s, i in zip(STAT_NAMES, ivs):
                    bit_options[s].add(i)

        # with the bit matches resolved, we just need to filter the actual IV possibilities
        for stat_name in STAT_NAMES:
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


def get_ranges(args: Namespace):
    basestats = utils.get_basestats(pokemon=args.pokemon, gen=args.generation)

    output: dict[str, tuple[str, str]] = {}

    for stat_name, base in zip(STAT_NAMES, basestats):
        is_hp = (stat_name == "HP")
        f = partial(
            utils.calculate_stat,
            level=args.level, base=base,
            hp=is_hp
        )

        minimum = f(iv=0, ev=0, nature=(1 if is_hp else 0.9))
        maximum_0 = f(iv=31, ev=0, nature=(1 if is_hp else 1.1))
        maximum_252 = f(iv=31, ev=252, nature=(1 if is_hp else 1.1))

        output[stat_name] = (str(minimum), f"{maximum_0} / {maximum_252}")

    # output back to UI
    for stat_name, (minimum, maximum) in output.items():
        args.ui[f"min_{stat_name}"].contents = minimum
        args.ui[f"max_{stat_name}"].contents = maximum


def show_base_stats(args: Namespace):
    basestats = utils.get_basestats(pokemon=args.pokemon, gen=args.generation)

    # output back to UI
    for stat_name, base in zip(STAT_NAMES, basestats):
        args.ui[f"base_{stat_name}"].contents = str(base)

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
        for stat_name in STAT_NAMES:
            widget = ui[f"ivs_{stat_name}"]
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
    frame.form: dict[str, EditableWidget] = dict()

    Label(master=frame, text="Generation*", anchor="center").grid(0, 0, opad=(5, 5))
    generation_options = ("8・VIII", "7・VII", "6・VI", "5・V", "4・IV", "3・III")
    frame.form["generation"] = Dropdown(master=frame, options=generation_options).grid(1, 0, opad=(5, 0))

    Label(master=frame, text="Pokémon*", anchor="center").grid(0, 1, opad=(0, 5))
    frame.form["pokémon"] = Textbox(master=frame).grid(1, 1, opad=(5, 0))

    Label(master=frame, text="Level*", anchor="center").grid(0, 2, opad=(0, 5))
    frame.form["level"] = Textbox(master=frame).grid(1, 2, opad=(5, 0))

    # row 2 is for the calculate button

    Label(master=frame, text="Minimum", anchor="center").grid(3, 1, opad=(5, 0))
    Label(master=frame, text="Maximum (0EV / 252EV)", anchor="center").grid(3, 2, opad=(5, 0))

    for row, stat_name in enumerate(STAT_NAMES, start=4):
        Label(master=frame, text=stat_name, anchor="e").grid(row, 0, opad=(5, 0))
        frame.form[f"min_{stat_name}"] = Textbox(master=frame).grid(row, 1)
        frame.form[f"max_{stat_name}"] = Textbox(master=frame).grid(row, 2)

    def ranges_button_callback():
        ui: dict[str, EditableWidget] = frame.form

        # clear the stat fields
        for stat_name in STAT_NAMES:
            ui[f"min_{stat_name}"].clear()
            ui[f"max_{stat_name}"].clear()

        # read generation from dropdown, converting, e.g. "4・IV" -> 4
        gen: int = int(ui["generation"].contents.split("・")[0])

        args = Namespace(
            ui=ui,  # passed so that check() can output back to the ui
            generation=gen,
            pokemon=ui["pokémon"].contents,
            level=int(ui["level"].contents)
        )
        get_ranges(args)


    Button(master=frame, text="Calculate Ranges", callback=ranges_button_callback).grid(2, 0, columnspan=3, opad=(5, 20))


def initialize_basestat_tab(frame: Frame) -> None:
    frame.form: dict[str, EditableWidget] = dict()

    Label(master=frame, text="Generation*", anchor="center").grid(0, 0, opad=(5, 5))
    generation_options = ("8・VIII", "7・VII", "6・VI", "5・V", "4・IV", "3・III")
    frame.form["generation"] = Dropdown(master=frame, options=generation_options).grid(1, 0, opad=(5, 0))

    Label(master=frame, text="Pokémon*", anchor="center").grid(0, 1, opad=(0, 5))
    frame.form["pokémon"] = Textbox(master=frame).grid(1, 1, opad=(5, 0))

    Label(master=frame, text="Base Stat", anchor="center").grid(3, 1, opad=(0, 5))
    for row, stat_name in enumerate(STAT_NAMES, start=4):
        Label(master=frame, text=stat_name, anchor="e").grid(row, 0, opad=(5, 0))
        frame.form[f"base_{stat_name}"] = Textbox(master=frame).grid(row, 1)

    def base_button_callback():
        ui: dict[str, EditableWidget] = frame.form

        # clear the stat fields
        for stat_name in STAT_NAMES:
            ui[f"base_{stat_name}"].clear()

        # read generation from dropdown, converting, e.g. "4・IV" -> 4
        gen: int = int(ui["generation"].contents.split("・")[0])

        args = Namespace(
            ui=ui,  # passed so that check() can output back to the ui
            generation=gen,
            pokemon=ui["pokémon"].contents
        )
        show_base_stats(args)

    Button(master=frame, text="Show Base Stats", callback=base_button_callback).grid(2, 0, columnspan=3, opad=(5, 20))


def main():
    config = Config.from_file(HERE / "config.json")

    window = Window(size=(730, 350), title=f"Pokémon IV Checker v{__version__}")
    
    # Activate the GUI color theme.
    # This must be done after the root window is created.
    theme = Theme.from_file(HERE / "themes" / f"{config.active_theme}.json")
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