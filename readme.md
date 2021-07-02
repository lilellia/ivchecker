# IVChecker

```
$ python3 main.py wimpod --level 23 --stats 51 30 26 13 19 43 --nature Adamant --characteristic "Takes plenty of siestas"
 HP [31]
Atk [30, 31]
Def [12, 13, 14, 15]
SpA [4, 5, 6, 7]
SpD [1, 2, 3, 4, 5]
Spe [6, 7, 8, 9]
```

Arguments:
- `pokemon`: The Pokémon's name/form. Regional forms use "A-" and "G-" prefixes for Alolan- and Galarian forms, respectively (e.g., A-Vulpix, G-Meowth). Mega evolutions use an "M-" prefix (e.g., M-Mawile). Most other forms use the form name as a suffix (e.g., Groudon-Primal or Pumpkaboo-Small). For a complete list, see basestats.csv.
- `-l/--level LEVEL`: the level of the Pokémon.
- `-s/--stats`: the current stats of the Pokémon, given in the order (HP, Attack, Defense, Special Attack, Special Defense, Speed).
- `-e/--evs`: the EVs for the Pokémon, given in the order (HP, Attack, Defense, Special Attack, Special Defense, Speed). This is optional, and if it is not given, all EVs are assumed to be zero.
- `-n/--nature`: the nature of the Pokémon. This must match exactly, but it is not case-sensitive.
- `-c/--char/--characteristic`: the characteristic of the Pokémon (e.g., "Quick to flee". This must be enclosed in quotation marks since it includes multiple words.) This value is optional and merely provides additional filtering.
- `-g/--generation`: The generation of the game in question (as an integer). If not given, this is assumed to be 8. This is used to account for base stat changes between generations.