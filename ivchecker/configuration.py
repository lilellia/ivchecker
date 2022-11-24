from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
import yaml


class NeutralNatureSortMethod(Enum):
    ALPHABETICAL = auto()
    STATWISE = auto()


@dataclass
class UIConfig:
    active_theme: str
    neutral_nature_sort: NeutralNatureSortMethod

    def __post_init__(self):
        if isinstance(self.neutral_nature_sort, str):
            self.neutral_nature_sort = NeutralNatureSortMethod[self.neutral_nature_sort.upper(
            )]


@dataclass
class GenerationConfig:
    most_recent: int
    min_supported: int


@dataclass
class IconConfig:
    main: str
    warning: str


@dataclass
class PathConfig:
    themes: str
    basestats: str
    characteristics: str
    natures: str
    statchanges: str
    icons: IconConfig

    def path_to_theme(self, theme: str) -> Path:
        return Path(self.themes) / f"{theme}.yaml"


@dataclass
class Config:
    ui: UIConfig
    generations: GenerationConfig
    paths: PathConfig

    @classmethod
    def from_yaml(cls, path: Path) -> "Config":
        raw = yaml.safe_load(path.read_text())

        ui = UIConfig(**raw["ui"])
        generations = GenerationConfig(**raw["generations"])

        # parse the nested dict -> IconConfig
        icons = IconConfig(**raw["paths"]["icons"])
        raw["paths"]["icons"] = icons

        paths = PathConfig(**raw["paths"])

        return cls(ui=ui, generations=generations, paths=paths)
