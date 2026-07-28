"""Configuration loader."""

from pathlib import Path

import yaml

DEFAULT_CONFIG = {
    "data_dir": "data",
    "output_dir": "output",
    "census_api_key": None,
    "target_year": 2020,
}


def load_config(path: Path | None = None) -> dict:
    cfg = dict(DEFAULT_CONFIG)
    if path is None:
        path = Path("config/sources.yaml")
    if path.exists():
        with open(path) as f:
            user_cfg = yaml.safe_load(f) or {}
        cfg.update(user_cfg)
    return cfg
