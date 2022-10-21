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
class PathConfig:
    themes: str
    basestats: str
    characteristics: str
    natures: str
    statchanges: str
    icon: str

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
        paths = PathConfig(**raw["paths"])

        return cls(ui=ui, generations=generations, paths=paths)
