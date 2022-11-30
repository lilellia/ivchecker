from dataclasses import dataclass
from pathlib import Path
import yaml


@dataclass
class UIConfig:
    textbox_relief: str


@dataclass
class GenerationConfig:
    most_recent: int
    min_supported: int


@dataclass
class PathConfig:
    basestats: str
    characteristics: str
    natures: str
    statchanges: str
    icon: str


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
        paths = PathConfig(**raw["paths"])

        return cls(ui=ui, generations=generations, paths=paths)
