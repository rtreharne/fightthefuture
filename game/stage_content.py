from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from django.conf import settings

from .constants import STAGE_COUNT


def _stage_config_path() -> Path:
    return Path(settings.BASE_DIR) / "game" / "stages.yaml"


@lru_cache(maxsize=8)
def _load_stage_config_cached(mtime_ns: int) -> dict:
    config_path = _stage_config_path()
    with config_path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, dict):
        return {}
    return loaded


def _load_stage_config() -> dict:
    config_path = _stage_config_path()
    try:
        mtime_ns = config_path.stat().st_mtime_ns
    except OSError:
        return {}
    return _load_stage_config_cached(mtime_ns)


def _apply_tokens(value, tokens: dict[str, str]):
    if isinstance(value, str):
        out = value
        for key, replacement in tokens.items():
            out = out.replace(key, replacement)
        return out
    if isinstance(value, list):
        return [_apply_tokens(item, tokens) for item in value]
    if isinstance(value, dict):
        return {key: _apply_tokens(item, tokens) for key, item in value.items()}
    return value


def get_stage_content(
    stage: int,
    language: str | None = None,
    tokens: dict[str, str] | None = None,
) -> dict:
    config = _load_stage_config()
    stages = config.get("stages", {}) if isinstance(config, dict) else {}

    raw = stages.get(stage)
    if raw is None:
        raw = stages.get(str(stage), {})
    if not isinstance(raw, dict):
        raw = {}

    title = raw.get("title") or f"Stage {stage}"
    has_dataset = bool(raw.get("has_dataset", True))
    narrative = raw.get("narrative")
    if narrative is not None:
        narrative = str(narrative)
    instructions = raw.get("instructions")
    if not isinstance(instructions, list):
        instructions = [str(instructions)] if instructions else []

    variant = None
    language_variants = raw.get("language_variants")
    if isinstance(language_variants, dict):
        key = (language or "").strip().lower()
        variant = language_variants.get(key) or language_variants.get("default")
        if not isinstance(variant, dict):
            variant = None

    content = {
        "stage": stage,
        "title": title,
        "has_dataset": has_dataset,
        "narrative": narrative,
        "instructions": instructions,
        "file_name": variant.get("file_name") if variant else None,
        "run_command": variant.get("run_command") if variant else None,
        "code": variant.get("code") if variant else None,
        "language": (language or "").lower() if language else None,
    }
    if tokens:
        return _apply_tokens(content, tokens)
    return content


def stage_has_dataset(stage: int) -> bool:
    if stage < 1 or stage > STAGE_COUNT:
        return False
    content = get_stage_content(stage, None)
    return bool(content.get("has_dataset", True))
