from __future__ import annotations

from dataclasses import dataclass
from itertools import count, takewhile
from pathlib import Path
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Generic, Protocol, TypeVar
import yaml

_T = TypeVar("_T")

def error(message=None, **options):
    messagebox.showerror("Error", message, **options)


class BaseWidget:
    wrapped_class = None

    def __init__(self, master: BaseWidget | None, *args: Any, **kwargs: Any):
        self.master = master

        if self.wrapped_class == tk.Tk:
            self._proxy = tk.Tk()
        elif master is None:
            self._proxy = self.wrapped_class(*args, **kwargs)
        else:
            self._proxy = self.wrapped_class(
                self.master._proxy, *args, **kwargs)

    def config(self, **options: Any):
        self._proxy.config(**options)
        return self


class Window(BaseWidget):
    wrapped_class = tk.Tk

    def __init__(self, size: tuple[int, int], title: str, master=None, **kwargs: Any):
        super().__init__(master=master, **kwargs)
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

    def set_icon(self, ico, include_children: bool = False) -> None:
        if isinstance(ico, (Path, str)):
            # load the image from file
            ico = ImageTk.PhotoImage(Image.open(ico))

        self._proxy.wm_iconphoto(include_children, ico)

    def run(self):
        self._proxy.mainloop()


class TopWindow(Window):
    wrapped_class = tk.Toplevel


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


class EditableWidget(Generic[_T], Protocol):
    @property
    def value(self) -> _T:
        """ Return the contents of the widget. """
        ...

    @value.setter
    def value(self, val: _T) -> None:
        """ Set the contents of the widget. """
        ...

    def clear(self) -> None:
        """ Clear the contents of the widget. """
        ...


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
    
    def __init__(self, master, *args, **kwargs) -> None:
        super().__init__(master, *args, **kwargs)

    @property
    def value(self) -> str:
        """ Return the text contents of the textbox. """
        return self._proxy.get()

    @value.setter
    def value(self, val: str) -> None:
        """ Set the text contents of the texbox. """
        self.clear()
        self._proxy.insert(0, val)

    def clear(self) -> None:
        """ Clear the contents of the textbox. """
        self._proxy.delete(0, tk.END)


class Dropdown(PositionableWidget):
    wrapped_class = ttk.Combobox

    def __init__(self, master: BaseWidget, options: tuple[str, ...], **kwargs):
        self._var = tk.StringVar(master._proxy, options[0])
        super().__init__(master, textvariable=self._var, **kwargs)

        self.options = tuple(options)
        self._proxy["values"] = self.options
        self._proxy["state"] = "readonly"

    @property
    def value(self) -> str:
        return self._var.get()

    @value.setter
    def value(self, val: str) -> None:
        """ Set the text contents of the dropdown. """
        self._var.set(val)

    def clear(self) -> None:
        self.value = ""


class Frame(PositionableWidget):
    wrapped_class = ttk.Frame

    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.form: dict[str, EditableWidget] = dict()


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
        

class Spinbox(PositionableWidget):
    wrapped_class = ttk.Spinbox
    
    def __init__(self, master, min: float, max: float, step: float = 1.0, *args, default: float | None = None, wrap: bool=False, **kwargs):
        self.min, self.max, self.step = min, max, step
        
        self._var = tk.StringVar()
        values = tuple(takewhile(max.__ge__, count(min, step)))
        
        super().__init__(master, from_=min, to=max, textvariable=self._var, values=values, wrap=wrap, *args, **kwargs)

        if default is not None:
            self.value = default
    
    @property
    def _raw_value(self) -> str:
        return self._var.get()
    
    @property
    def value(self) -> float:
        return float(self._var.get())
    
    @value.setter
    def value(self, val: float) -> None:
        self._var.set(str(val))
        
    def clear(self) -> None:
        self.value = self.min