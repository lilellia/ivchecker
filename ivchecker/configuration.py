from dataclasses import dataclass
from pathlib import Path
import yaml


@dataclass
class UIConfig:
    active_theme: str


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
