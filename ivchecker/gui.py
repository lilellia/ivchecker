from dataclasses import dataclass
from pathlib import Path
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk
from typing import Protocol
import yaml


class BaseWidget:
    wrapped_class = None

    def __init__(self, master, *args, **kwargs):
        self.master = master

        if self.wrapped_class == tk.Tk:
            self._proxy = tk.Tk()
        else:
            self._proxy = self.wrapped_class(self.master._proxy, *args, **kwargs)

    def config(self, **options):
        self._proxy.config(**options)
        return self


class Window(BaseWidget):
    wrapped_class = tk.Tk

    def __init__(self, size: tuple[int, int], title: str, **kwargs):
        super().__init__(master=None, **kwargs)
        self.size = size
        self.title = title

    @property
    def width(self) -> int:
        """ Return the width of the window. """
        return self._proxy.winfo_width()

    @property
    def height(self) -> int:
        """ Return the height of the window. """
        return self._proxy.winfo_height()
    @property
    def size(self) -> tuple[int, int]:
        """ Return the size of the window: (width, height). """
        return self.width, self.height

    @size.setter
    def size(self, val: tuple[int, int]) -> None:
        """ Set the size of the window: (width, height). """
        self._proxy.geometry("{}x{}".format(*val))

    @width.setter
    def width(self, val: int) -> None:
        """ Set the width of the window. """
        self.size = val, self.height
    
    @height.setter
    def height(self, val: int) -> None:
        """ Set the height of the window. """
        self.size = self.width, val
    
    @property
    def title(self) -> str:
        """ Get the window title. """
        return self._proxy.title()

    @title.setter
    def title(self, val: str) -> None:
        """ Set the window title. """
        self._proxy.title(val)

    def set_icon(self, ico: ImageTk.PhotoImage | Path | str) -> None:
        if isinstance(ico, (Path, str)):
            # load the image from file
            ico = ImageTk.PhotoImage(Image.open(ico))

        self._proxy.wm_iconphoto(True, ico)

    def run(self):
        self._proxy.mainloop()


class PositionableWidget(BaseWidget):
    def pack(self, expand=True, fill=None, side=tk.TOP):
        self._proxy.pack(expand=expand, fill=fill, side=side)
        return self

    def grid(self, row: int, column: int, rowspan: int = 1, columnspan: int = 1, ipad: tuple[int, int] = (0, 0), opad: tuple[int, int] = (0, 0), sticky: str = "nsew"):
        self._proxy.grid(
            row=row, column=column,
            rowspan=rowspan, columnspan=columnspan,
            ipadx=ipad[0], ipady=ipad[1],
            padx=opad[0], pady=opad[1],
            sticky=sticky
        )
        return self


class ToggleWidget(BaseWidget):
    @property
    def is_enabled(self) -> bool:
        """ Return True if the widget is enabled; False otherwise. """
        return (self._proxy.state == tk.ACTIVE)

    def enable(self):
        """ Enable the widget. """
        self._proxy.state = tk.ACTIVE

    def disable(self):
        """ Disable the widget. """
        self._proxy.state = tk.DISABLED

    def toggle(self):
        """ Toggle the state of the widget. """
        if self.is_enabled:
            self.disable()
        else:
            self.enable()

class EditableWidget(Protocol):
    @property
    def contents(self) -> str:
        """ Return the contents of the widget. """

    @contents.setter
    def contents(self, val: str) -> None:
        """ Set the contents of the widget. """

    def clear(self) -> None:
        """ Clear the contents of the widget. """


class Label(PositionableWidget):
    wrapped_class = ttk.Label

    def __init__(self, master, text: str, **kwargs) -> None:
        super().__init__(master=master, text=str(text), **kwargs)
        self._text = text

    @property
    def text(self) -> str:
        """ Return the text contents of the label. """
        return self._text

    @text.setter
    def text(self, val: str) -> None:
        """ Set the text contents of the label. """
        self.config(text=val)

class Textbox(PositionableWidget, ToggleWidget):
    wrapped_class = tk.Entry

    @property
    def contents(self) -> str:
        """ Return the text contents of the textbox. """
        return self._proxy.get()

    @contents.setter
    def contents(self, val: str) -> None:
        """ Set the text contents of the texbox. """
        self.clear()
        self._proxy.insert(0, val)

    def clear(self) -> None:
        """ Clear the contents of the textbox. """
        self._proxy.delete(0, tk.END)


class Dropdown(PositionableWidget):
    wrapped_class = ttk.Combobox

    def __init__(self, master: BaseWidget, options: tuple[str], **kwargs):
        self._var = tk.StringVar(master._proxy, options[0])
        super().__init__(master, textvariable=self._var, **kwargs)
        
        self.options = tuple(options)
        self._proxy["values"] = self.options
        self._proxy["state"] = "readonly"

    @property
    def contents(self) -> str:
        return self._var.get()

    @contents.setter
    def contents(self, val: str) -> None:
        """ Set the text contents of the dropdown. """
        self._var.set(val)

    def clear(self) -> None:
        self.contents = ""


class Frame(PositionableWidget):
    wrapped_class = ttk.Frame


class TabbedDisplay(PositionableWidget):
    wrapped_class = ttk.Notebook

    def __init__(self, master, *args, **kwargs) -> None:
        super().__init__(master, *args, **kwargs)
        self.tabs = []
    
    def add_tab(self, text: str) -> Frame:
        """ Add a tab to the display. """
        frame = Frame(master=self)
        frame.pack(fill=tk.BOTH, expand=True)
        self._proxy.add(frame._proxy, text=text)

        self.tabs.append(frame)
        return frame

    def add_tabs(self, *labels: str) -> list[Frame]:
        """ Add multiple tabs at once. """
        return [self.add_tab(label) for label in labels]


class Button(PositionableWidget, ToggleWidget):
    wrapped_class = ttk.Button

    def __init__(self, master, text, callback, **kwargs):
        super().__init__(master, text=text, command=callback, **kwargs)

    def __call__(self):
        """ Call the button's callback and return that function's return value.
        Has no effect if the button is disabled or if there is no callback.
        """
        return self._proxy.invoke()

    def flash(self) -> None:
        """ Cause the button to flash several times between active/normal colors. """
        self._proxy.flash()


@dataclass
class Theme:
    background: str
    text_color: str
    accent: str
    alt_accent: str

    @classmethod
    def from_yaml(cls, path: Path) -> "Theme":
        data = yaml.safe_load(path.read_text())
        return cls(**data)

    def _get_proxy(self, *, name: str = "lil") -> ttk.Style:
        style = ttk.Style()
        style.theme_create(
            name, parent="alt",
            settings={
                "TNotebook": {
                    "configure": {
                        "background": self.background,
                        "tabmargins": (2, 5, 2, 0),
                    }
                },
                "TNotebook.Tab": {
                    "configure": {
                        "padding": (5, 1),
                        "background": self.background,
                        "foreground": self.text_color
                    },
                    "map": {
                        "background": [
                            ("selected", self.accent),
                        ],
                        "expand": [("selected", (1, 1, 1, 0))]
                    }
                },
                "TFrame": {
                    "configure": {
                        "background": self.background
                    }
                },
                "TLabel": {
                    "configure": {
                        "background": self.background,
                        "foreground": self.text_color
                    }
                },
                "TButton": {
                    "configure": {
                        "background": self.alt_accent,
                        "relief": "raised",
                        "anchor": "center"
                    },
                    "map": {
                        "background": [("active", self.accent)]
                    }
                },
                "TCombobox": {
                    "configure": {
                        "fieldbackground": self.background,
                        "background": self.background,
                        "foreground": self.text_color,
                        "selectforeground": self.text_color
                    }
                }
            }
        )
        return style

    def use(self, *, name: str = "lil") -> None:
        """ Activate the theme. """
        self._get_proxy().theme_use(name)