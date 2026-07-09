from __future__ import annotations

from pathlib import Path
from typing import Any


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "configs" / "polymarket_paper_btc_15m.yaml"


def load_runtime_config(path: Path | None = None) -> dict[str, Any]:
    try:
        import yaml
    except ModuleNotFoundError as exc:
        raise SystemExit("PyYAML is required to load the runtime config YAML") from exc
    config_path = path or DEFAULT_CONFIG_PATH
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise SystemExit("runtime config YAML must be a mapping")
    return data


def configured_move_threshold_pct(path: Path | None = None) -> float:
    config = load_runtime_config(path)
    try:
        return float(config["strategy"]["move_threshold_pct"])
    except (KeyError, TypeError, ValueError) as exc:
        raise SystemExit("runtime config YAML must define strategy.move_threshold_pct") from exc
