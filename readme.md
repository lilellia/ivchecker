# IVChecker

## Installation & Usage

Tested in Python 3.9, but it should support Python 3.7+.

```bash
# to install
$ git clone https://github.com/lilellia/ivchecker.git
$ cd ivchecker
$ python3 -m pip install -r requirements.txt

# to use:
$ python3 main.py
```

## Changelog

- **v2.2.0** (2022-11-27)
    - Redesigned UI, including rdbende's [Forest-ttk theme](https://github.com/rdbende/Forest-ttk-theme).
    - In accordance with UI update, project now includes a `ttk.Spinbox` wrapper.
    - Removal of "Show Basestats" tab in favor of just adding that data to the "Show Ranges" tab.
    - Code cleanup and removal of superfluous assets and imports, etc.
    - README is actually updated now.
- **v2.1.3** (2022-11-25)
    - Added custom error message with characteristic and invalid stat values. Previously, the error read `max() arg is an empty sequence` when trying to cap invalid stats.
- **v2.1.2** (2022-11-24)
    - Check IVs tab now shows nature effects instead of just the nature name. For example, "Adamant" → "Adamant (+Atk/-SpA)"; "Serious" → "Serious (±)".
    - Neutral natures are now shown in the nature table, rather than in their own list.
    - Restructured `natures.csv` to store raised/lowered stats, rather than the float modifiers for each stat.
    - Backend code now uses `Nature` and `Characteristic` classes, as well as defining `__mod__` for Nature objects, which allows `nature % stat` to grab the modifier instead of `nature.modifiers[stat]`.
- **v2.1.1** (2022-11-18)
    - Basestat tab now shows BST.
- **v2.1.0** (2022-11-18)
    - Added Generation IX support.
    - Added fuzzy matching for Pokémon names. The error message shows the two closest neighbors.
- **v2.0** (2022-11-17)
    - Fixed various bugs.
    - Added Info tab.

- **v2.0β**
    - Moved to `tkinter` ui framework over a command-line interface.
