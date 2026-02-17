from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

SECTION_PATTERN = re.compile(r"^\[([A-Z0-9_]+)\]\s*$")


class ContentSourceError(RuntimeError):
    """Raised when the unified text source is malformed or incomplete."""


def read_text_source(path: str | Path) -> str:
    text_path = Path(path)
    if not text_path.exists():
        raise ContentSourceError(
            f"Не найден единый источник контента: {text_path}. "
            "Создайте файл input_texts/text.txt с нужными секциями."
        )
    return text_path.read_text(encoding="utf-8")


def parse_sections(raw_text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current: str | None = None

    for line in raw_text.splitlines():
        match = SECTION_PATTERN.match(line.strip())
        if match:
            current = match.group(1)
            sections[current] = []
            continue
        if current is not None:
            sections[current].append(line)

    return {name: "\n".join(lines).strip() for name, lines in sections.items()}


def require_sections(sections: dict[str, str], required: list[str]) -> None:
    missing = [name for name in required if name not in sections or not sections[name].strip()]
    if missing:
        hints = ", ".join(f"[{name}]" for name in missing)
        raise ContentSourceError(
            "В input_texts/text.txt не хватает обязательных секций: "
            f"{hints}. Добавьте их и повторите генерацию."
        )


def parse_key_values(block: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in block.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        result[key.strip()] = value.strip()
    return result


def split_semicolon_list(raw_value: str | None) -> list[str]:
    if not raw_value:
        return []
    return [item.strip() for item in raw_value.split(";") if item.strip()]


def parse_segments(section_text: str) -> list[dict[str, Any]]:
    segments: list[dict[str, Any]] = []
    buffer: list[str] = []
    in_segment = False

    for line in section_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == "SEGMENT":
            in_segment = True
            buffer = []
            continue
        if stripped == "END":
            if in_segment:
                kv = parse_key_values("\n".join(buffer))
                segments.append(
                    {
                        "segment_id": kv.get("id", ""),
                        "name": kv.get("name", ""),
                        "who": kv.get("who", ""),
                        "job_to_be_done": kv.get("job", kv.get("job_to_be_done", "")),
                        "pains": split_semicolon_list(kv.get("pains")),
                        "triggers": split_semicolon_list(kv.get("triggers")),
                        "taboos": split_semicolon_list(kv.get("taboos")),
                        "tone_hint": kv.get("tone_hint", ""),
                        "cta_style": kv.get("cta_style", ""),
                        "example_offer_adaptations": split_semicolon_list(
                            kv.get("example_offer_adaptations")
                        ),
                    }
                )
            in_segment = False
            buffer = []
            continue
        if in_segment:
            buffer.append(stripped)

    return segments


def parse_formats(section_text: str) -> list[dict[str, Any]]:
    formats: list[dict[str, Any]] = []
    buffer: list[str] = []
    in_format = False

    for line in section_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == "FORMAT":
            in_format = True
            buffer = []
            continue
        if stripped == "END":
            if in_format:
                kv = parse_key_values("\n".join(buffer))
                headline_max = int(kv.get("headline_max", "0"))
                body_max = int(kv.get("body_max", "0"))
                notes = kv.get("notes", "")
                formats.append(
                    {
                        "format_id": kv.get("id", ""),
                        "name": kv.get("name", ""),
                        "limits": {
                            "headline_max": headline_max,
                            "body_max": body_max,
                        },
                        "output_template": (
                            f"Сделай headline до {headline_max} символов и body до {body_max} символов."
                        ),
                        "notes": notes,
                    }
                )
            in_format = False
            buffer = []
            continue
        if in_format:
            buffer.append(stripped)

    return formats


def parse_slides(section_text: str) -> list[dict[str, Any]]:
    slides: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    for line in section_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("SLIDE "):
            if current:
                slides.append(current)
            try:
                slide_number = int(stripped.split(" ", 1)[1])
            except ValueError as exc:
                raise ContentSourceError(f"Некорректный номер слайда: {stripped}") from exc
            current = {"number": slide_number}
            continue
        if current is None or "=" not in stripped:
            continue

        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key == "bullets":
            current[key] = [item.strip() for item in value.split("|") if item.strip()]
        else:
            current[key] = value

    if current:
        slides.append(current)

    slides.sort(key=lambda item: item["number"])
    return slides


def parse_json_section(section_text: str, section_name: str) -> dict[str, Any]:
    try:
        return json.loads(section_text)
    except json.JSONDecodeError as exc:
        raise ContentSourceError(
            f"Секция [{section_name}] содержит невалидный JSON: {exc.msg} (строка {exc.lineno})."
        ) from exc


def build_sample_input_text(kv: dict[str, str]) -> str:
    lines = [
        f"title={kv.get('title', '')}",
        f"base_text={kv.get('base_text', '')}",
        f"product_context={kv.get('product_context', '')}",
        f"selected_segments={kv.get('selected_segments', '')}",
        f"tone={kv.get('tone', '')}",
        f"format_id={kv.get('format_id', '')}",
        f"variants_per_segment={kv.get('variants_per_segment', '')}",
        f"variability_level={kv.get('variability_level', '')}",
        f"constraints={kv.get('constraints', '')}",
    ]
    return "\n".join(lines) + "\n"


def demo_steps_to_markdown(step_map: dict[str, str]) -> str:
    numbered_keys = sorted(
        (key for key in step_map.keys() if key.startswith("step_")),
        key=lambda item: int(item.split("_", 1)[1]),
    )
    lines = ["# Demo script (3-4 минуты)", "", "## Сценарий показа", ""]
    for key in numbered_keys:
        step_index = int(key.split("_", 1)[1])
        lines.append(f"{step_index}. {step_map[key]}")
    lines.append("")
    lines.append("## Что показать в финале")
    lines.append("- Таблица вариаций по сегментам")
    lines.append("- Risk-метки и как их чинить")
    lines.append("- Экспорт в CSV/JSON")
    lines.append("")
    return "\n".join(lines)


def enforce_char_counts(payload: dict[str, Any]) -> dict[str, Any]:
    for segment in payload.get("segments", []):
        for copy in segment.get("copies", []):
            headline = copy.get("headline", "")
            body = copy.get("body", "")
            copy["char_count"] = {
                "headline": len(headline),
                "body": len(body),
            }
            copy.setdefault("risk_flags", [])
    return payload


def ensure_format_limits(
    payload: dict[str, Any],
    format_limits: dict[str, dict[str, int]],
) -> dict[str, Any]:
    format_id = payload.get("input_echo", {}).get("format_id", "")
    limits = format_limits.get(format_id)
    if not limits:
        return payload

    headline_max = limits["headline_max"]
    body_max = limits["body_max"]

    for segment in payload.get("segments", []):
        for copy in segment.get("copies", []):
            headline = copy.get("headline", "")
            body = copy.get("body", "")
            overflow = False
            if len(headline) > headline_max:
                copy["headline"] = headline[:headline_max].rstrip()
                overflow = True
            if len(body) > body_max:
                copy["body"] = body[:body_max].rstrip()
                overflow = True

            if overflow:
                risk_flags = copy.setdefault("risk_flags", [])
                risk_flags.append(
                    {
                        "type": "format_overflow",
                        "note": "Текст был автоматически укорочен под лимит формата.",
                        "suggest_fix": (
                            "Сократить формулировку вручную и сохранить ключевую мысль без потери смысла."
                        ),
                    }
                )

    return enforce_char_counts(payload)
