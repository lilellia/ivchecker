from ivchecker.configuration import Config
from ivchecker.engine import Characteristic, HPType, Nature, Stat, get_basestats
from ivchecker.gui import (
    error,
    Button,
    Dropdown,
    EditableWidget,
    Frame,
    Label,
    Spinbox,
    Textbox,
)
from ivchecker.runners import check_ivs, get_ranges
from ivchecker.utils import format_ivs

GENERATION_OPTIONS = ("9・IX", "8・VIII", "7・VII",
                      "6・VI", "5・V", "4・IV", "3・III")


def initialize_check_tab(frame: Frame, *, config: Config) -> None:
    form: dict[str, EditableWidget] = dict()
    frame.form = form
    relief: str = config.ui.textbox_relief

    Label(master=frame, text="Generation*", anchor="e").grid(0, 1, columnspan=2, opad=(5, 0))
    frame.form["generation"] = Dropdown(master=frame, options=GENERATION_OPTIONS).grid(0, 3, columnspan=4)
    
    Label(master=frame, text="Pokémon*", anchor="center").grid(1, 1, columnspan=3, opad=(0, 0))
    frame.form["pokémon"] = Textbox(master=frame, relief=relief).grid(2, 1, columnspan=3)

    Label(master=frame, text="Level*", anchor="center").grid(1, 4, columnspan=3)
    frame.form["level"] = Spinbox(
        master=frame,
        min=1, max=100, step=1, default=1,
        width=10
    ).grid(2, 4, columnspan=3)

    Label(master=frame, text="Stats*", anchor="e").grid(4, 0, opad=(5, 0))
    for j, stat in enumerate(Stat, start=1):
        Label(master=frame, text=stat.value, anchor="center").grid(row=3, column=j, opad=(0, 10))
        frame.form[f"stat_{stat.value}"] = Textbox(master=frame, width=7, justify="center", relief=relief) \
            .grid(row=4, column=j, opad=(0, 2))

    Label(master=frame, text="EVs*", anchor="e").grid(5, 0, opad=(5, 0))
    for j, stat in enumerate(Stat, start=1):
        frame.form[f"ev_{stat.value}"] = Textbox(master=frame, width=7, justify="center", relief=relief) \
            .grid(row=5, column=j, opad=(0, 2))
        frame.form[f"ev_{stat.value}"].value = "0"
    
    nature_options = ("",) + tuple(sorted(map(str, Nature.read_all())))
    Label(master=frame, text="Nature*", anchor="e").grid(6, 1, columnspan=2, opad=(5, 0))
    frame.form["nature"] = Dropdown(master=frame, options=nature_options).grid(6, 3, columnspan=4, opad=(0, 2))
    
    char_options = ("",) + tuple(sorted(Characteristic.read_all()))
    Label(master=frame, text="Characteristic", anchor="e").grid(7, 1, columnspan=2, opad=(5, 2))
    frame.form["char"] = Dropdown(master=frame, options=char_options).grid(7, 3, columnspan=4, opad=(0, 2))
    
    hp_types = ("",) + tuple(sorted(t.name.title() for t in HPType))
    Label(master=frame, text="HP Type", anchor="e").grid(8, 1, columnspan=2, opad=(5, 2))
    frame.form["hp-type"] = Dropdown(master=frame, options=hp_types).grid(8, 3, columnspan=4, opad=(0, 2))
    
    Label(master=frame, text="IVs", anchor="e").grid(11, 0, opad=(5, 0))
    for j, stat in enumerate(Stat, start=1):
        Label(master=frame, text=stat.value, anchor="center").grid(row=10, column=j)
        frame.form[f"iv_{stat.value}"] = Textbox(master=frame, width=7, justify="center", relief=relief) \
            .grid(row=11, column=j)

    def check_button_callback():
        ui: dict[str, EditableWidget] = frame.form
        
        # clear the IV fields
        for stat in Stat:
            widget = ui[f"iv_{stat.value}"]
            widget.clear()
            
        # read generation from dropdown, converting, e.g. "4・IV" -> 4
        gen: int = int(ui["generation"].value.split("・")[0])
        
        # read stats
        actual_stats: list[int] = []
        evs: list[int] = []
        
        for stat in Stat:
            actual = ui[f"stat_{stat.value}"].value
            ev = ui[f"ev_{stat.value}"].value
            
            try:
                actual_stats.append(int(actual))
            except ValueError:
                error(f"Invalid value for {stat.value}: {actual!r}")
                return
                
            try:
                evs.append(int(ev))
            except ValueError:
                error(f"Invalid value for {stat.value} EV: {ev!r}")
                return
        
        # read level
        level = int(ui["level"].value)
        
        # read nature from textbox, but remove the +/- comment
        nature_name, *_ = ui["nature"].value.split()
        
        # read characteristic from textbox, but convert to a Characteristic object
        description = ui["char"].value
        char = Characteristic.get(description) if description else None
        
        try:
            ivs = check_ivs(
                pokemon=ui["pokémon"].value,
                generation=gen,
                level=level,
                actual_stats=tuple(actual_stats),
                evs=tuple(evs),
                nature_name=nature_name,
                characteristic=char,
                hidden_power_type=ui["hp-type"].value
            )
        except ValueError as e:
            error(e)
            return
        
        # and now output back to the ui
        for stat, iv in zip(Stat, ivs):
            ui[f"iv_{stat.value}"].value = format_ivs(iv)
            

    Button(master=frame, text="Calculate IVs", callback=check_button_callback, style="Accent.TButton") \
        .grid(row=9, column=1, columnspan=6, opad=(0, 8))


def initialize_ranges_tab(frame: Frame, *, config: Config) -> None:
    form: dict[str, EditableWidget] = dict()
    frame.form = form
    relief: str = config.ui.textbox_relief

    Label(master=frame, text="Generation*", width=8, anchor="center").grid(0, 0, opad=(5, 5))
    frame.form["generation"] = Dropdown(master=frame, options=GENERATION_OPTIONS, width=8) \
        .grid(1, 0, opad=(5, 0))

    Label(master=frame, text="Pokémon*", anchor="center", width=8).grid(0, 1, columnspan=3, opad=(0, 5))
    frame.form["pokémon"] = Textbox(master=frame, relief=relief, width=8).grid(1, 1, columnspan=3, opad=(5, 0))

    Label(master=frame, text="Level*", anchor="center", width=8).grid(0, 4, opad=(0, 5))
    frame.form["level"] = Spinbox(
        master=frame,
        min=1, max=100, step=1, default=1,
        width=6
    ).grid(1, 4)

    # row 2 is for the calculate button

    label_cfg = dict(anchor="w", width=6)
    Label(master=frame, text="Base", **label_cfg).grid(3, 1, rowspan=2, opad=(5, 0))
    Label(master=frame, text="Min", **label_cfg).grid(3, 2, rowspan=2, opad=(5, 0))
    Label(master=frame, text="Max", **label_cfg).grid(3, 3, opad=(5, 0))
    Label(master=frame, text="(0EV)", **label_cfg).grid(4, 3, opad=(5, 0))
    Label(master=frame, text="Max", **label_cfg).grid(3, 4, opad=(5, 0))
    Label(master=frame, text="(252EV)", **label_cfg).grid(4, 4, opad=(5, 0))

    for row, stat in enumerate(Stat, start=5):
        Label(master=frame, text=stat.value, width=8, anchor="e").grid(row, 0, opad=(10, 0))
        frame.form[f"base_{stat.value}"] = Textbox(master=frame, relief=relief, width=8).grid(row, 1)
        frame.form[f"min_{stat.value}"] = Textbox(master=frame, relief=relief, width=8).grid(row, 2)
        frame.form[f"max0_{stat.value}"] = Textbox(master=frame, relief=relief, width=8).grid(row, 3)
        frame.form[f"max252_{stat.value}"] = Textbox(master=frame, relief=relief, width=8).grid(row, 4)
        
    frame.form["bst"] = Textbox(master=frame, relief=relief, width=8).grid(11, 1)

    def ranges_button_callback():
        ui: dict[str, EditableWidget] = frame.form

        # clear the stat fields
        for stat in Stat:
            ui[f"base_{stat.value}"].clear()
            ui[f"min_{stat.value}"].clear()
            ui[f"max0_{stat.value}"].clear()
            ui[f"max252_{stat.value}"].clear()
        ui["bst"].clear()

        # read generation from dropdown, converting, e.g. "4・IV" -> 4
        gen: int = int(ui["generation"].value.split("・")[0], 10)
        basestats = get_basestats(pokemon=ui["pokémon"].value, generation=gen)
        
        # output basestats to UI first
        for stat, base in zip(Stat, basestats):
            ui[f"base_{stat.value}"].value = str(base)
        ui["bst"].value = f"BST:{sum(basestats)}"

        # level
        assert isinstance(ui["level"], Spinbox)
        try:
            level_val = ui["level"]._raw_value
            level = int(level_val)
        except ValueError:
            error(f"Cannot parse level: {ui['level']._raw_value!r}")
            return

        try:
            ranges = get_ranges(pokemon=ui["pokémon"].value, generation=gen, level=level)
        except ValueError as e:
            error(e)
            return

        # output data back to ui
        for stat, base, (min, max0, max252) in zip(Stat, basestats, ranges):
            ui[f"min_{stat.value}"].value = str(min)
            ui[f"max0_{stat.value}"].value = str(max0)
            ui[f"max252_{stat.value}"].value = str(max252)

    Button(master=frame, text="Calculate Ranges", callback=ranges_button_callback, style="Accent.TButton") \
        .grid(2, 0, columnspan=5, opad=(0, 20))


def initialize_basestat_tab(frame: Frame, *, config: Config) -> None:
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
        gen: int = int(ui["generation"].value.split("・")[0])

        try:
            basestats = get_basestats(
                pokemon=ui["pokémon"].value, generation=gen)
        except ValueError as e:
            error(e)
            return

        # output back to ui
        for stat, base in zip(Stat, basestats):
            ui[f"base_{stat.value}"].value = str(base)

        ui[f"bst"].value = str(sum(basestats))

    Button(master=frame, text="Show Base Stats", callback=base_button_callback).grid(
        2, 0, columnspan=3, opad=(5, 20)
    )


def initialize_info_tab(frame: Frame, *, config: Config) -> None:
    STAT_COLORS = {
        Stat.ATK.value: "#f5ac78",
        Stat.DEF.value: "#fae078",
        Stat.SPA.value: "#9db7f5",
        Stat.SPD.value: "#a7db8d",
        Stat.SPE.value: "#fa92b2"
    }
    DIM_COLOR = "#606060"
    LIGHT_COLOR = "#e8e8e8"

    # set up headers
    Label(frame, text="(±10%)", anchor="c", foreground=DIM_COLOR) \
        .grid(row=0, column=0)

    for i, stat in enumerate(list(Stat)[1:], start=1):
        color = STAT_COLORS[stat.value]
        cfg = dict(background=color, foreground="#313131", anchor="c")
        Label(frame, text=f"{stat.value}↓", **cfg) \
            .grid(row=0, column=i, ipad=(0, 7), opad=(0, 5))
        Label(frame, text=f"{stat.value}↑", **cfg) \
            .grid(row=i, column=0, ipad=(10, 5), opad=(5, 0))

    natures = tuple(Nature.read_all())
    for row, raised in enumerate(list(Stat)[1:], start=1):
        for col, lowered in enumerate(list(Stat)[1:], start=1):
            fg = DIM_COLOR if raised == lowered else LIGHT_COLOR
            for nature in natures:
                if nature.raised == raised and nature.lowered == lowered:
                    Label(frame, text=nature.name.title(),
                          anchor="c", foreground=fg).grid(row=row, column=col, ipad=(10, 0))
