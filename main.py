from pathlib import Path
import sys
import tkinter as tk
from tkinter import ttk

from ivchecker.configuration import Config
from ivchecker.gui import TabbedDisplay, Window
from ivchecker.tabinit import initialize_basestat_tab, initialize_check_tab, initialize_ranges_tab, initialize_info_tab

__version__ = '2.2.0'

# path to this folder
HERE = Path(__file__).parent


def main():
    if "--version" in sys.argv:
        print(__version__)
        return

    config = Config.from_yaml(HERE / "config.yaml")

    window = Window(size=(450, 470),
                    title=f"Pokémon IV Checker v{__version__}")
    window.set_icon(config.paths.icon)

    # Activate the GUI color theme.
    window._proxy.call("source", "assets/forest-dark.tcl")
    ttk.Style().theme_use("forest-dark")

    # Create the tab display and its tabs.
    tab_display = TabbedDisplay(master=window)
    tab_display.pack(expand=True, fill="both")
    
    tabs = tab_display.add_tabs("Check IVs", "Show Ranges", "Info")
    tab_initializers = [initialize_check_tab, initialize_ranges_tab, initialize_info_tab]
    
    for tab, init in zip(tabs, tab_initializers):
        init(tab, config=config)

    # Actually run the application
    window.run()


if __name__ == '__main__':
    main()
