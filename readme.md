# IVChecker

Call signature:
```bash
$ python3 main.py POKEMON [-g generation] [-v] SUBCOMMAND ...
```

where `SUBCOMMAND` is one of `check`, `ranges`, and `base` and `POKEMON` is the Pokémon's name/form. Regional forms use "A-" and "G-" prefixes for Alolan- and Galarian forms, respectively (e.g., A-Vulpix, G-Meowth). Mega evolutions use an "M-" prefix (e.g., M-Mawile). Most other forms use the form name as a suffix (e.g., Groudon-Primal or Pumpkaboo-Small). For a complete list, see basestats.csv.

The `-g/--gen` flag can be passed before the subcommand to change the game's generation. This is used to account for base stat changes between Pokémon. If this is not passed, generation 8 stats are used.

The `-v/--verbose` flag can be passed before the subcommand to enable verbose output. Currently, this is only applied with the "check" subcommand.


## check IVs for a Pokémon
```
$ python3 main.py wimpod check --level 23 --stats 51 30 26 13 19 43 --nature Adamant --characteristic "Takes plenty of siestas"
╒═════╤══════╤═══════╤═══════╤═══════╤═══════╤═══════╕
│     │   HP │ Atk   │ Def   │ SpA   │ SpD   │ Spe   │
╞═════╪══════╪═══════╪═══════╪═══════╪═══════╪═══════╡
│ IVs │   31 │ 30-31 │ 12-15 │ 4-7   │ 1-5   │ 6-9   │
╘═════╧══════╧═══════╧═══════╧═══════╧═══════╧═══════╛

$ python3 main.py wimpod -v check --level 23 --stats 51 30 26 13 19 43 --nature Adamant --characteristic "Takes plenty of siestas"
╒════════╤══════╤═══════╤═══════╤═══════╤═══════╤═══════╕
│        │ HP   │ Atk   │ Def   │ SpA   │ SpD   │ Spe   │
╞════════╪══════╪═══════╪═══════╪═══════╪═══════╪═══════╡
│ Nature │      │ +++   │       │ ---   │       │       │
├────────┼──────┼───────┼───────┼───────┼───────┼───────┤
│ Base   │ 25   │ 35    │ 40    │ 20    │ 30    │ 80    │
├────────┼──────┼───────┼───────┼───────┼───────┼───────┤
│ IVs    │ 31   │ 30-31 │ 12-15 │ 4-7   │ 1-5   │ 6-9   │
╘════════╧══════╧═══════╧═══════╧═══════╧═══════╧═══════╛

$ python3 main.py wimpod -v check -l 23 -s 51 30 26 13 19 43 -n Adamant -c 'takes plenty of siestas' -hp bug
╒════════╤══════╤═══════╤═══════╤═══════════╤════════════╤═══════╕
│        │ HP   │ Atk   │ Def   │ SpA       │ SpD        │ Spe   │
╞════════╪══════╪═══════╪═══════╪═══════════╪════════════╪═══════╡
│ Nature │      │ +++   │       │ ---       │            │       │
├────────┼──────┼───────┼───────┼───────────┼────────────┼───────┤
│ Base   │ 25   │ 35    │ 40    │ 20        │ 30         │ 80    │
├────────┼──────┼───────┼───────┼───────────┼────────────┼───────┤
│ IVs    │ 31   │ 30-31 │ 12-15 │ 5-7 (odd) │ 2-4 (even) │ 6-9   │
╘════════╧══════╧═══════╧═══════╧═══════════╧════════════╧═══════╛
```

Arguments:
- `-l/--level LEVEL`: the level of the Pokémon.
- `-s/--stats`: the current stats of the Pokémon, given in the order (HP, Attack, Defense, Special Attack, Special Defense, Speed).
- `-e/--evs`: the EVs for the Pokémon, given in the order (HP, Attack, Defense, Special Attack, Special Defense, Speed). This is optional, and if it is not given, all EVs are assumed to be zero.
- `-n/--nature`: the nature of the Pokémon. This must match exactly, but it is not case-sensitive.
- `-c/--char/--characteristic`: the characteristic of the Pokémon (e.g., "Quick to flee". This must be enclosed in quotation marks since it includes multiple words.) This value is optional and merely provides additional filtering.
- `-hp/--hidden-power`: The known Hidden Power type. This is optional and only used for additional filtering.
- `-v/--verbose`: When this flag is passed, the nature modifier (+Atk/-SpA) and base stats are also shown. This flag must be passed BEFORE the "check" subcommand.

## determine possible ranges for stats

```
$ python3 main.py vivillon ranges --level 38
╒══════════╤══════╤══════╤═══════╤═══════╤═══════╤═══════╤═══════╕
│ Nature   │   IV │   HP │   Atk │   Def │   SpA │   SpD │   Spe │
╞══════════╪══════╪══════╪═══════╪═══════╪═══════╪═══════╪═══════╡
│ ---      │    0 │  108 │    39 │    38 │    65 │    38 │    64 │
├──────────┼──────┼──────┼───────┼───────┼───────┼───────┼───────┤
│ neutral  │    0 │  108 │    44 │    43 │    73 │    43 │    72 │
├──────────┼──────┼──────┼───────┼───────┼───────┼───────┼───────┤
│ neutral  │   31 │  120 │    56 │    54 │    85 │    54 │    84 │
├──────────┼──────┼──────┼───────┼───────┼───────┼───────┼───────┤
│ +++      │   31 │  120 │    61 │    59 │    93 │    59 │    92 │
╘══════════╧══════╧══════╧═══════╧═══════╧═══════╧═══════╧═══════╛
```

This means that a level-38 Vivillon could have an attack stat between 39 (-Atk, 0IV, 0EV), 44 (neutral Atk nature, 0IV, 0EV), 56 (neutral Atk nature, 31IV, 0EV) and 61 (+Atk, 31IV, 0EV).

Arguments:
- `-l/--level LEVEL`: the level of the Pokémon.

## show base stats

```bash
$ python3 main.py a-vulpix base
╒══════════╤══════╤═══════╤═══════╤═══════╤═══════╤═══════╕
│          │   HP │   Atk │   Def │   SpA │   SpD │   Spe │
╞══════════╪══════╪═══════╪═══════╪═══════╪═══════╪═══════╡
│ A-Vulpix │   38 │    41 │    40 │    50 │    65 │    65 │
╘══════════╧══════╧═══════╧═══════╧═══════╧═══════╧═══════╛
```