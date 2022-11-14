from pathlib import Path

from ivchecker.configuration import Config
from ivchecker.gui import TabbedDisplay, Theme, Window
from ivchecker.tabinit import initialize_basestat_tab, initialize_check_tab, initialize_ranges_tab, initialize_info_tab
import ivchecker.utils as utils

__version__ = '2.0β2'

# path to this folder
HERE = Path(__file__).parent


def main():
    config = Config.from_yaml(HERE / "config.yaml")

    window = Window(size=(730, 350),
                    title=f"Pokémon IV Checker v{__version__}")
    window.set_icon(config.paths.icon)

    # Activate the GUI color theme.
    # This must be done after the root window is created.
    active_theme = Theme.from_yaml(
        HERE / config.paths.path_to_theme(config.ui.active_theme)
    )
    active_theme.use()

    # Create the tab display and its tabs.
    tabs = TabbedDisplay(master=window)
    tabs.pack(expand=True, fill="both")
    check_tab, ranges_tab, basestat_tab, info_tab = tabs.add_tabs(
        "Check IVs", "Show Ranges", "Show Base Stats", "Info")

    # Initialize the tabs individually.
    initialize_check_tab(check_tab)
    initialize_ranges_tab(ranges_tab)
    initialize_basestat_tab(basestat_tab)
    initialize_info_tab(info_tab, theme=active_theme)

    # Actually run the application
    window.run()


if __name__ == '__main__':
    main()
