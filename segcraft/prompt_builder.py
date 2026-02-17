from __future__ import annotations

import json
from typing import Any


def _format_segment_block(segment: dict[str, Any]) -> str:
    return (
        f"- Segment: {segment.get('name', '')} ({segment.get('segment_id', '')})\n"
        f"  who: {segment.get('who', '')}\n"
        f"  pains: {', '.join(segment.get('pains', []))}\n"
        f"  triggers: {', '.join(segment.get('triggers', []))}\n"
        f"  taboos: {', '.join(segment.get('taboos', []))}\n"
        f"  tone_hint: {segment.get('tone_hint', '')}\n"
        f"  cta_style: {segment.get('cta_style', '')}"
    )


def _schema_hint() -> str:
    required_keys = {
        "version": "string",
        "input_echo": {
            "base_text": "string",
            "tone": "friendly|neutral|formal|bold",
            "format_id": "string",
            "variants_per_segment": "number",
            "constraints": ["string"],
            "assumptions": ["string"],
        },
        "questions": [{"q": "string", "why": "string", "priority": "P0|P1|P2"}],
        "segments": [
            {
                "segment_id": "string",
                "segment_name": "string",
                "core_insight": "string",
                "trigger": "string",
                "angle": "string",
                "copies": [
                    {
                        "headline": "string",
                        "body": "string",
                        "cta": "string",
                        "rationale": "string",
                        "char_count": {"headline": "number", "body": "number"},
                        "risk_flags": [{"type": "string", "note": "string", "suggest_fix": "string"}],
                    }
                ],
                "differences_note": "string",
            }
        ],
        "global_risks": [{"risk": "string", "impact": "string", "mitigation": "string"}],
        "export_hints": {"how_to_use": ["string"], "ab_test_suggestions": ["string"]},
        "exec_summary": {"for_marketer": "string", "for_non_tech_manager": "string"},
    }
    return json.dumps(required_keys, ensure_ascii=False, indent=2)


def build_case_bundle(
    base_text: str,
    context: str,
    selected_segments: list[dict[str, Any]],
    format_spec: dict[str, Any],
    constraints: list[str],
    tone: str,
    language: str,
    variants_per_segment: int,
    variability_level: str,
) -> str:
    segment_blocks = "\n".join(_format_segment_block(segment) for segment in selected_segments)

    limits = format_spec.get("limits", {})
    headline_max = limits.get("headline_max", 999)
    body_max = limits.get("body_max", 5000)

    constraints_text = "\n".join(f"- {item}" for item in constraints) if constraints else "- Нет"

    return f"""[ROLE]
Ты — редактор и маркетолог. Генерируй вариации текста под сегменты.
Не выдумывай факты. Соблюдай ограничения и лимиты.
Верни строго JSON по схеме. Никаких пояснений вне JSON.

[BASE_TEXT]
{base_text}

[CONTEXT]
{context or 'Не указан'}

[LANGUAGE]
{language}

[TONE]
{tone}

[SEGMENTS_SELECTED]
{segment_blocks}

[FORMAT]
format_id: {format_spec.get('format_id', '')}
name: {format_spec.get('name', '')}
headline_max: {headline_max}
body_max: {body_max}
notes: {format_spec.get('notes', '')}
output_template: {format_spec.get('output_template', '')}

[CONSTRAINTS]
{constraints_text}

[VARIANTS_PER_SEGMENT]
{variants_per_segment}

[VARIABILITY_LEVEL]
{variability_level}

[OUTPUT_SCHEMA]
{_schema_hint()}

Важно:
1) segments.length должно быть равно числу выбранных сегментов.
2) copies.length должно быть равно variants_per_segment.
3) Обязательно считай char_count.
4) Для рисков используй типы: forbidden_claims, compliance_sensitive, vague_offer, missing_proof, format_overflow.
5) Если текст превышает лимиты — укороти. Если не удалось, ставь format_overflow с suggest_fix.
"""
