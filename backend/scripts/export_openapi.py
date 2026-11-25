"""Writes backend/openapi.json, the contract the frontend types are generated from."""

import json
import sys
from pathlib import Path

from apan.core.config import Environment, Settings
from apan.main import create_app

OUTPUT = Path(__file__).resolve().parents[1] / "openapi.json"


def render() -> str:
    settings = Settings.model_validate({"app_env": Environment.TEST})
    return json.dumps(create_app(settings).openapi(), indent=2, ensure_ascii=False) + "\n"


if __name__ == "__main__":
    OUTPUT.write_text(render(), encoding="utf-8", newline="\n")
    sys.stdout.write(f"Wrote {OUTPUT}\n")
