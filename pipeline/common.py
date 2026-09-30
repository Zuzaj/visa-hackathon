"""Shared helpers: config loading, paths. No business logic here."""
import pathlib

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load_config() -> dict:
    with open(ROOT / "config.yaml") as f:
        return yaml.safe_load(f)


def path(rel: str) -> pathlib.Path:
    return ROOT / rel
