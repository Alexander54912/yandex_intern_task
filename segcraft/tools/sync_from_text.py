#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from content_source import (
    ContentSourceError,
    build_sample_input_text,
    demo_steps_to_markdown,
    enforce_char_counts,
    ensure_format_limits,
    parse_formats,
    parse_json_section,
    parse_key_values,
    parse_sections,
    parse_segments,
    parse_slides,
    read_text_source,
    require_sections,
)

TEXT_SOURCE = PROJECT_ROOT / "input_texts" / "text.txt"

REQUIRED_SECTIONS = [
    "PROJECT_META",
    "DEFAULT_SEGMENTS",
    "AD_FORMATS",
    "SAMPLE_INPUT_1",
    "SAMPLE_INPUT_2",
    "SAMPLE_OUTPUT_1_JSON",
    "SAMPLE_OUTPUT_2_JSON",
    "DEMO_SCRIPT",
    "SLIDES",
    "SUBMISSION_ANSWERS_MD",
    "PITCH_1PAGER_MD",
]


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_deck_config(
    meta: dict[str, str],
    slides: list[dict],
) -> dict:
    image_map = {
        5: "assets/flow_diagram.png",
        7: "assets/ui_mock_1.png",
        8: "assets/ui_mock_2.png",
        9: "assets/table_mock.png",
    }
    return {
        "project": {
            "name": meta.get("name", "SegCraft"),
            "tagline": meta.get("tagline", ""),
            "one_liner": meta.get("one_liner", ""),
        },
        "style": {
            "bg_color": "FFFFFF",
            "text_color": "111111",
            "accent_color": "FF3333",
            "title_font": "Arial",
            "body_font": "Arial",
        },
        "slides": [
            {
                "number": slide["number"],
                "title": slide.get("title", ""),
                "bullets": slide.get("bullets", []),
                "notes": slide.get("notes", ""),
                "image": image_map.get(slide["number"], ""),
            }
            for slide in slides
        ],
    }


def validate_minimums(segments: list[dict], formats: list[dict], slides: list[dict]) -> None:
    if len(segments) < 7:
        raise ContentSourceError(
            f"В [DEFAULT_SEGMENTS] найдено только {len(segments)} сегментов. Нужно минимум 7."
        )
    if len(formats) < 4:
        raise ContentSourceError(
            f"В [AD_FORMATS] найдено только {len(formats)} форматов. Нужно минимум 4."
        )
    if len(slides) < 12:
        raise ContentSourceError(
            f"В [SLIDES] найдено только {len(slides)} слайдов. Нужно минимум 12."
        )


def main() -> None:
    raw_text = read_text_source(TEXT_SOURCE)
    sections = parse_sections(raw_text)
    require_sections(sections, REQUIRED_SECTIONS)

    meta = parse_key_values(sections["PROJECT_META"])
    segments = parse_segments(sections["DEFAULT_SEGMENTS"])
    formats = parse_formats(sections["AD_FORMATS"])
    slides = parse_slides(sections["SLIDES"])

    validate_minimums(segments, formats, slides)

    format_limits = {
        fmt["format_id"]: {
            "headline_max": int(fmt["limits"]["headline_max"]),
            "body_max": int(fmt["limits"]["body_max"]),
        }
        for fmt in formats
    }

    sample_input_1 = parse_key_values(sections["SAMPLE_INPUT_1"])
    sample_input_2 = parse_key_values(sections["SAMPLE_INPUT_2"])

    sample_output_1 = parse_json_section(sections["SAMPLE_OUTPUT_1_JSON"], "SAMPLE_OUTPUT_1_JSON")
    sample_output_2 = parse_json_section(sections["SAMPLE_OUTPUT_2_JSON"], "SAMPLE_OUTPUT_2_JSON")

    sample_output_1 = ensure_format_limits(enforce_char_counts(sample_output_1), format_limits)
    sample_output_2 = ensure_format_limits(enforce_char_counts(sample_output_2), format_limits)

    write_json(PROJECT_ROOT / "segments" / "default_segments_ru.json", segments)
    write_json(PROJECT_ROOT / "formats" / "ad_formats_ru.json", formats)

    write_text(PROJECT_ROOT / "samples" / "sample_input_1_ru.txt", build_sample_input_text(sample_input_1))
    write_text(PROJECT_ROOT / "samples" / "sample_input_2_ru.txt", build_sample_input_text(sample_input_2))
    write_json(PROJECT_ROOT / "samples" / "sample_output_1.json", sample_output_1)
    write_json(PROJECT_ROOT / "samples" / "sample_output_2.json", sample_output_2)

    demo_steps = parse_key_values(sections["DEMO_SCRIPT"])
    write_text(PROJECT_ROOT / "submission" / "demo_script.md", demo_steps_to_markdown(demo_steps))
    write_text(PROJECT_ROOT / "submission" / "answers.md", sections["SUBMISSION_ANSWERS_MD"].strip() + "\n")
    write_text(PROJECT_ROOT / "submission" / "pitch_1pager.md", sections["PITCH_1PAGER_MD"].strip() + "\n")

    deck_config = build_deck_config(meta, slides)
    write_json(PROJECT_ROOT / "deck" / "deck_config.json", deck_config)

    print("[sync] Контент успешно собран из input_texts/text.txt")
    print("[sync] Сгенерированы: segments/, formats/, samples/, submission/, deck/deck_config.json")


if __name__ == "__main__":
    try:
        main()
    except ContentSourceError as exc:
        print(f"[sync:error] {exc}")
        raise SystemExit(1)
