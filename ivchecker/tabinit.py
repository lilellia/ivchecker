from itertools import count
from ivchecker.gui import Button, Dropdown, EditableWidget, Frame, Label, Textbox, Theme
from ivchecker.runners import check_ivs, get_ranges
from ivchecker.utils import STAT_NAMES, format_ivs, get_all_characteristics, get_basestats, get_nature, get_all_natures, HiddenPowerType


def initialize_check_tab(frame: Frame) -> None:
    form: dict[str, EditableWidget] = dict()
    frame.form = form

    Label(master=frame, text="Generation*", anchor="e").grid(0, 0, opad=(5, 0))
    generation_options = ("8・VIII", "7・VII", "6・VI", "5・V", "4・IV", "3・III")
    frame.form["generation"] = Dropdown(
        master=frame, options=generation_options).grid(0, 1, columnspan=2)

    Label(master=frame, text="Pokémon*", anchor="e").grid(1, 0, opad=(5, 0))
    frame.form["pokémon"] = Textbox(master=frame).grid(1, 1, columnspan=6)

    Label(master=frame, text="Level*", anchor="e").grid(2, 0, opad=(5, 0))
    frame.form["level"] = Textbox(master=frame).grid(2, 1, columnspan=6)

    Label(master=frame, text="Stats*", anchor="e").grid(4, 0, opad=(5, 0))
    for j, stat in enumerate(STAT_NAMES, start=1):
        Label(master=frame, text=stat, anchor="center").grid(row=3, column=j)
        frame.form[f"stat_{stat}"] = Textbox(
            master=frame).config(width=4).grid(row=4, column=j)

    Label(master=frame, text="EVs", anchor="e").grid(5, 0, opad=(5, 0))
    for j, stat in enumerate(STAT_NAMES, start=1):
        frame.form[f"evs_{stat}"] = Textbox(
            master=frame).config(width=4).grid(row=5, column=j)
        frame.form[f"evs_{stat}"].contents = "0"  # set default value of 0

    Label(master=frame, text="Nature*",
          anchor="center").grid(6, 1, columnspan=2, opad=(0, 5))
    natures = ("",) + get_all_natures()
    frame.form["nature"] = Dropdown(
        master=frame, options=natures).grid(7, 1, columnspan=2)

    Label(master=frame, text="Characteristic", anchor="center").grid(
        6, 3, columnspan=2, opad=(0, 5))
    characteristics = ("",) + get_all_characteristics()
    frame.form["characteristic"] = Dropdown(
        master=frame, options=characteristics).grid(7, 3, columnspan=2)

    Label(master=frame, text="HP Type", anchor="center").grid(
        6, 5, columnspan=2, opad=(0, 5))
    types = ("",) + tuple(sorted(t.name.title() for t in HiddenPowerType))
    frame.form["hidden-power-type"] = Dropdown(
        master=frame, options=types).grid(7, 5, columnspan=2)

    Label(master=frame, text="IVs", anchor="e").grid(11, 0, opad=(5, 0))
    for j, stat in enumerate(STAT_NAMES, start=1):
        Label(master=frame, text=stat, anchor="center").grid(row=10, column=j)
        frame.form[f"ivs_{stat}"] = Textbox(
            master=frame).config(width=12).grid(row=11, column=j)

    def check_button_callback():
        ui: dict[str, EditableWidget] = frame.form

        # clear the IV fields
        for stat_name in STAT_NAMES:
            widget = ui[f"ivs_{stat_name}"]
            widget.clear()

        # read generation from dropdown, converting, e.g. "4・IV" -> 4
        gen: int = int(ui["generation"].contents.split("・")[0])

        actual_stats = (ui[f"stat_{stat}"].contents for stat in STAT_NAMES)
        evs = (ui[f"evs_{stat}"].contents for stat in STAT_NAMES)

        ivs = check_ivs(
            pokemon=ui["pokémon"].contents,
            generation=gen,
            level=int(ui["level"].contents),
            actual_stats=tuple(map(int, actual_stats)),
            evs=tuple(map(int, evs)),
            nature_name=ui["nature"].contents,
            characteristic=ui["characteristic"].contents,
            hidden_power_type=ui["hidden-power-type"].contents
        )

        for stat, iv in zip(STAT_NAMES, ivs):
            ui[f"ivs_{stat}"].contents = format_ivs(iv)

    Button(master=frame, text="Calculate IVs", callback=check_button_callback).grid(
        9, 1, columnspan=6, opad=(0, 20))


def initialize_ranges_tab(frame: Frame) -> None:
    frame.form: dict[str, EditableWidget] = dict()

    Label(master=frame, text="Generation*",
          anchor="center").grid(0, 0, opad=(5, 5))
    generation_options = ("8・VIII", "7・VII", "6・VI", "5・V", "4・IV", "3・III")
    frame.form["generation"] = Dropdown(
        master=frame, options=generation_options).grid(1, 0, opad=(5, 0))

    Label(master=frame, text="Pokémon*",
          anchor="center").grid(0, 1, opad=(0, 5))
    frame.form["pokémon"] = Textbox(master=frame).grid(1, 1, opad=(5, 0))

    Label(master=frame, text="Level*", anchor="center").grid(0, 2, opad=(0, 5))
    frame.form["level"] = Textbox(master=frame).grid(1, 2, opad=(5, 0))

    # row 2 is for the calculate button

    Label(master=frame, text="Minimum", anchor="center").grid(3, 1, opad=(5, 0))
    Label(master=frame, text="Maximum (0EV / 252EV)",
          anchor="center").grid(3, 2, opad=(5, 0))

    for row, stat_name in enumerate(STAT_NAMES, start=4):
        Label(master=frame, text=stat_name,
              anchor="e").grid(row, 0, opad=(5, 0))
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

        ranges = get_ranges(
            pokemon=ui["pokémon"].contents, generation=gen, level=int(ui["level"].contents))

        # output data back to ui
        for stat, (min, max) in zip(STAT_NAMES, ranges):
            ui[f"min_{stat}"].contents = min
            ui[f"max_{stat}"].contents = max

    Button(master=frame, text="Calculate Ranges",
           callback=ranges_button_callback).grid(2, 0, columnspan=3, opad=(5, 20))


def initialize_basestat_tab(frame: Frame) -> None:
    frame.form: dict[str, EditableWidget] = dict()

    Label(master=frame, text="Generation*",
          anchor="center").grid(0, 0, opad=(5, 5))
    generation_options = ("8・VIII", "7・VII", "6・VI", "5・V", "4・IV", "3・III")
    frame.form["generation"] = Dropdown(
        master=frame, options=generation_options).grid(1, 0, opad=(5, 0))

    Label(master=frame, text="Pokémon*",
          anchor="center").grid(0, 1, opad=(0, 5))
    frame.form["pokémon"] = Textbox(master=frame).grid(1, 1, opad=(5, 0))

    Label(master=frame, text="Base Stat",
          anchor="center").grid(3, 1, opad=(0, 5))
    for row, stat_name in enumerate(STAT_NAMES, start=4):
        Label(master=frame, text=stat_name,
              anchor="e").grid(row, 0, opad=(5, 0))
        frame.form[f"base_{stat_name}"] = Textbox(master=frame).grid(row, 1)

    def base_button_callback():
        ui: dict[str, EditableWidget] = frame.form

        # clear the stat fields
        for stat_name in STAT_NAMES:
            ui[f"base_{stat_name}"].clear()

        # read generation from dropdown, converting, e.g. "4・IV" -> 4
        gen: int = int(ui["generation"].contents.split("・")[0])

        basestats = get_basestats(
            pokemon=ui["pokémon"].contents, generation=gen)

        # output back to ui
        for stat_name, base in zip(STAT_NAMES, basestats):
            ui[f"base_{stat_name}"].contents = str(base)

    Button(master=frame, text="Show Base Stats", callback=base_button_callback).grid(
        2, 0, columnspan=3, opad=(5, 20))


def initialize_info_tab(frame: Frame, theme: Theme) -> None:
    natures = {name: get_nature(name)
               for name in get_all_natures()}

    # set up headers
    Label(frame, text="(±10%)", anchor="c",
          foreground="#606060").grid(row=0, column=0)
    for i, stat in enumerate(STAT_NAMES[1:], start=1):
        color = theme.stat_colors[stat]
        cfg = dict(background=color, foreground="#313131", anchor="c")
        Label(frame, text=f"{stat}↓", **
              cfg).grid(row=0, column=i, ipad=(0, 7), opad=(0, 5))
        Label(frame, text=f"{stat}↑", **
              cfg).grid(row=i, column=0, ipad=(10, 0), opad=(5, 0))

    # get all the "interesting" natures
    for row, _ in enumerate(STAT_NAMES[1:], start=1):
        for col, _ in enumerate(STAT_NAMES[1:], start=1):
            if row == col:
                Label(frame, text="—", anchor="c").grid(row=row, column=col)
                continue

            targets = [name for name, modifiers in natures.items() if modifiers[row]
                       == 1.1 and modifiers[col] == 0.9]
            Label(frame, text="・".join(targets),
                  anchor="c").grid(row=row, column=col, ipad=(10, 0))

    # get the neutral natures
    neutral_col = len(STAT_NAMES)
    Label(frame, text="Neutral Natures", anchor="c").grid(
        row=0, column=neutral_col, opad=(12, 0))
    neutrals = [name for name, modifiers in natures.items() if set(modifiers) == {
        1.0}]
    for i, neutral in enumerate(neutrals, start=1):
        Label(frame, text=neutral, anchor="c").grid(
            row=i, column=neutral_col, opad=(12, 0))
