from pathlib import Path
import re

from ivchecker.configuration import Config
from ivchecker.engine import Characteristic, HPType, Nature, Stat, get_basestats
from ivchecker.gui import (
    error,
    Button,
    Dropdown,
    EditableWidget,
    Frame,
    Label,
    Textbox,
    Theme,
)
from ivchecker.runners import check_ivs, get_ranges
from ivchecker.utils import format_ivs

GENERATION_OPTIONS = ("9・IX", "8・VIII", "7・VII",
                      "6・VI", "5・V", "4・IV", "3・III")


def initialize_check_tab(frame: Frame, config: Config) -> None:
    form: dict[str, EditableWidget] = dict()
    frame.form = form

    Label(master=frame, text="Generation*", anchor="e").grid(0, 0, opad=(5, 0))
    frame.form["generation"] = Dropdown(master=frame, options=GENERATION_OPTIONS).grid(
        0, 1, columnspan=2
    )

    Label(master=frame, text="Pokémon*", anchor="e").grid(1, 0, opad=(5, 0))
    frame.form["pokémon"] = Textbox(master=frame).grid(1, 1, columnspan=6)

    Label(master=frame, text="Level*", anchor="e").grid(2, 0, opad=(5, 0))
    frame.form["level"] = Textbox(master=frame).grid(2, 1, columnspan=6)

    Label(master=frame, text="Stats*", anchor="e").grid(4, 0, opad=(5, 0))
    for j, stat in enumerate(Stat, start=1):
        Label(master=frame, text=stat.value, anchor="center").grid(row=3, column=j)
        frame.form[f"stat_{stat.value}"] = (
            Textbox(master=frame).config(width=4).grid(row=4, column=j)
        )

    Label(master=frame, text="EVs", anchor="e").grid(5, 0, opad=(5, 0))
    for j, stat in enumerate(Stat, start=1):
        frame.form[f"evs_{stat.value}"] = (
            Textbox(master=frame).config(width=4).grid(row=5, column=j)
        )
        frame.form[f"evs_{stat.value}"].contents = "0"  # set default value of 0

    Label(master=frame, text="Nature*", anchor="center").grid(
        6, 1, columnspan=2, opad=(0, 5)
    )

    natures = ("",) + tuple(sorted(map(str, Nature.read_all())))
    frame.form["nature"] = Dropdown(master=frame, options=natures).grid(
        7, 1, columnspan=2
    )

    Label(master=frame, text="Characteristic", anchor="center").grid(
        6, 3, columnspan=2, opad=(0, 5)
    )
    characteristics = ("",) + tuple(sorted(c for c in Characteristic.read_all()))
    frame.form["characteristic"] = Dropdown(master=frame, options=characteristics).grid(
        7, 3, columnspan=2
    )

    Label(master=frame, text="HP Type", anchor="center").grid(
        6, 5, columnspan=2, opad=(0, 5)
    )
    types = ("",) + tuple(sorted(t.name.title() for t in HPType))
    frame.form["hidden-power-type"] = Dropdown(master=frame, options=types).grid(
        7, 5, columnspan=2
    )

    Label(master=frame, text="IVs", anchor="e").grid(11, 0, opad=(5, 0))
    for j, stat in enumerate(Stat, start=1):
        Label(master=frame, text=stat.value, anchor="center").grid(row=10, column=j)
        frame.form[f"ivs_{stat.value}"] = (
            Textbox(master=frame).config(width=12).grid(row=11, column=j)
        )

    def check_button_callback():
        ui: dict[str, EditableWidget] = frame.form

        # clear the IV fields
        for stat in Stat:
            widget = ui[f"ivs_{stat.value}"]
            widget.clear()

        # read generation from dropdown, converting, e.g. "4・IV" -> 4
        gen: int = int(ui["generation"].contents.split("・")[0])

        actual_stats: list[int] = []
        evs: list[int] = []
        for stat in Stat:
            stat_val = ui[f"stat_{stat.value}"].contents
            ev_val = ui[f"evs_{stat.value}"].contents
            try:
                actual_stats.append(int(stat_val))
            except ValueError:
                error(f"Invalid value for {stat.value}: {stat_val!r}")
                return

            try:
                evs.append(int(ev_val))
            except ValueError:
                error(f"Invalid value for {stat.value} EV: {ev_val!r}")
                return

        try:
            level = int(ui["level"].contents)
        except ValueError:
            error(f"Invalid value for level: {ui['level'].contents!r}")
            return

        # read nature from textbox, converting, e.g., "Adamant (+Atk/-SpA)"
        # to just "Adamant"
        nature_name, *_ = ui["nature"].contents.split()
        
        # read Characteristic from textbox, converting to Characteristic object
        description = ui["characteristic"].contents
        characteristic = Characteristic.get(description) if description else None

        try:
            ivs = check_ivs(
                pokemon=ui["pokémon"].contents,
                generation=gen,
                level=level,
                actual_stats=tuple(actual_stats),
                evs=tuple(evs),
                nature_name=nature_name,
                characteristic=characteristic,
                hidden_power_type=ui["hidden-power-type"].contents,
            )
        except ValueError as e:
            error(e)
            return

        for stat, iv in zip(Stat, ivs):
            ui[f"ivs_{stat.value}"].contents = format_ivs(iv)

    Button(master=frame, text="Calculate IVs", callback=check_button_callback).grid(
        9, 1, columnspan=6, opad=(0, 20)
    )


def initialize_ranges_tab(frame: Frame, config: Config) -> None:
    frame.form: dict[str, EditableWidget] = dict()

    Label(master=frame, text="Generation*",
          anchor="center").grid(0, 0, opad=(5, 5))
    frame.form["generation"] = Dropdown(master=frame, options=GENERATION_OPTIONS).grid(
        1, 0, opad=(5, 0)
    )

    Label(master=frame, text="Pokémon*",
          anchor="center").grid(0, 1, opad=(0, 5))
    frame.form["pokémon"] = Textbox(master=frame).grid(1, 1, opad=(5, 0))

    Label(master=frame, text="Level*", anchor="center").grid(0, 2, opad=(0, 5))
    frame.form["level"] = Textbox(master=frame).grid(1, 2, opad=(5, 0))

    # row 2 is for the calculate button

    Label(master=frame, text="Minimum", anchor="center").grid(3, 1, opad=(5, 0))
    Label(master=frame, text="Maximum (0EV / 252EV)", anchor="center") \
        .grid(3, 2, opad=(5, 0))

    for row, stat in enumerate(Stat, start=4):
        Label(master=frame, text=stat.value,
              anchor="e").grid(row, 0, opad=(5, 0))
        frame.form[f"min_{stat.value}"] = Textbox(master=frame).grid(row, 1)
        frame.form[f"max_{stat.value}"] = Textbox(master=frame).grid(row, 2)

    def ranges_button_callback():
        ui: dict[str, EditableWidget] = frame.form

        # clear the stat fields
        for stat in Stat:
            ui[f"min_{stat.value}"].clear()
            ui[f"max_{stat.value}"].clear()

        # read generation from dropdown, converting, e.g. "4・IV" -> 4
        gen: int = int(ui["generation"].contents.split("・")[0], 10)

        # level
        level_val = ui["level"].contents
        try:
            level = int(level_val)
        except ValueError:
            error(f"Cannot parse level: {level_val!r}")
            return

        try:
            ranges = get_ranges(
                pokemon=ui["pokémon"].contents, generation=gen, level=level
            )
        except ValueError as e:
            error(e)
            return

        # output data back to ui
        for stat, (min, max) in zip(Stat, ranges):
            ui[f"max_{stat.value}"].contents = max
            ui[f"min_{stat.value}"].contents = min

    Button(master=frame, text="Calculate Ranges", callback=ranges_button_callback) \
        .grid(2, 0, columnspan=3, opad=(5, 20))


def initialize_basestat_tab(frame: Frame, config: Config) -> None:
    Label(master=frame, text="Generation*",
          anchor="center").grid(0, 0, opad=(5, 5))
    frame.form["generation"] = Dropdown(master=frame, options=GENERATION_OPTIONS) \
        .grid(1, 0, opad=(5, 0))

    Label(master=frame, text="Pokémon*",
          anchor="center").grid(0, 1, opad=(0, 5))
    frame.form["pokémon"] = Textbox(master=frame).grid(1, 1, opad=(5, 0))

    Label(master=frame, text="Base Stat", anchor="center") \
        .grid(3, 1, opad=(0, 5))
    for row, stat in enumerate(Stat, start=4):
        Label(master=frame, text=stat.value,
              anchor="e").grid(row, 0, opad=(5, 0))
        frame.form[f"base_{stat.value}"] = Textbox(master=frame).grid(row, 1)

    total_row = 4 + len(Stat)
    Label(master=frame, text="Total", anchor="e").grid(total_row, 0)
    frame.form[f"bst"] = Textbox(master=frame).grid(total_row, 1)

    def base_button_callback():
        ui: dict[str, EditableWidget] = frame.form

        # clear the stat fields
        for stat in Stat:
            ui[f"base_{stat.value}"].clear()
        ui["bst"].clear()

        # read generation from dropdown, converting, e.g. "4・IV" -> 4
        gen: int = int(ui["generation"].contents.split("・")[0])

        try:
            basestats = get_basestats(
                pokemon=ui["pokémon"].contents, generation=gen)
        except ValueError as e:
            error(e)
            return

        # output back to ui
        for stat, base in zip(Stat, basestats):
            ui[f"base_{stat.value}"].contents = str(base)

        ui[f"bst"].contents = str(sum(basestats))

    Button(master=frame, text="Show Base Stats", callback=base_button_callback).grid(
        2, 0, columnspan=3, opad=(5, 20)
    )


def initialize_info_tab(frame: Frame, config: Config) -> None:
    theme_path = Path(__file__).parent.parent / \
        config.paths.path_to_theme(config.ui.active_theme)
    theme = Theme.from_yaml(theme_path)

    # set up headers
    Label(frame, text="(±10%)", anchor="c", foreground=theme.dim_color) \
        .grid(row=0, column=0)

    for i, stat in enumerate(list(Stat)[1:], start=1):
        color = theme.stat_colors[stat.value]
        cfg = dict(background=color, foreground="#313131", anchor="c")
        Label(frame, text=f"{stat.value}↓", **cfg) \
            .grid(row=0, column=i, ipad=(0, 7), opad=(0, 5))
        Label(frame, text=f"{stat.value}↑", **cfg) \
            .grid(row=i, column=0, ipad=(10, 5), opad=(5, 0))

    natures = tuple(Nature.read_all())
    for row, raised in enumerate(list(Stat)[1:], start=1):
        for col, lowered in enumerate(list(Stat)[1:], start=1):
            fg = theme.dim_color if raised == lowered else theme.text_color
            for nature in natures:
                if nature.raised == raised and nature.lowered == lowered:
                    Label(frame, text=nature.name.title(),
                          anchor="c", foreground=fg).grid(row=row, column=col, ipad=(10, 0))
