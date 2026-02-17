from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic import ValidationError

from schemas import SegCraftResponse

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None


class LLMClientError(RuntimeError):
    """Generic LLM client error."""


class LLMValidationError(LLMClientError):
    """Raised when model output cannot be validated after repair."""


def get_client() -> Any | None:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None
    if OpenAI is None:
        raise LLMClientError(
            "OPENAI_API_KEY задан, но пакет openai не установлен. "
            "Установите зависимости из requirements.txt."
        )
    return OpenAI(api_key=api_key)


def _extract_first_json_object(raw_text: str) -> str:
    text = raw_text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.replace("json\n", "", 1).strip()

    try:
        json.loads(text)
        return text
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    if start == -1:
        raise LLMValidationError("В ответе модели нет JSON-объекта.")

    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]

    raise LLMValidationError("Не удалось выделить полный JSON из ответа модели.")


def parse_and_validate(raw_text: str) -> SegCraftResponse:
    json_text = _extract_first_json_object(raw_text)
    payload = json.loads(json_text)
    return SegCraftResponse.model_validate(payload)


def generate(prompt_text: str, model_name: str | None = None) -> str:
    client = get_client()
    if client is None:
        raise LLMClientError("OPENAI_API_KEY не найден. Включите mock mode.")

    model = model_name or os.getenv("MODEL_NAME", "gpt-4o-mini")
    response = client.responses.create(
        model=model,
        input=prompt_text,
        temperature=0.35,
    )
    raw_text = getattr(response, "output_text", "")
    if raw_text:
        return raw_text

    # Fallback for SDK variants where output_text might be empty.
    parts: list[str] = []
    for item in getattr(response, "output", []):
        for content in getattr(item, "content", []):
            text_value = getattr(content, "text", None)
            if text_value:
                parts.append(text_value)
    combined = "\n".join(parts).strip()
    if not combined:
        raise LLMClientError("LLM вернул пустой ответ.")
    return combined


def repair_json(raw_text: str, validation_error: Exception, model_name: str | None = None) -> str:
    client = get_client()
    if client is None:
        raise LLMClientError("OPENAI_API_KEY не найден. Repair невозможен в mock mode.")

    model = model_name or os.getenv("MODEL_NAME", "gpt-4o-mini")
    repair_prompt = (
        "Исправь JSON. Верни ТОЛЬКО валидный JSON без markdown и пояснений.\n\n"
        f"Ошибка валидации:\n{validation_error}\n\n"
        f"Текущий ответ:\n{raw_text}"
    )
    response = client.responses.create(
        model=model,
        input=repair_prompt,
        temperature=0,
    )
    fixed = getattr(response, "output_text", "").strip()
    if not fixed:
        raise LLMClientError("Repair attempt вернул пустой ответ.")
    return fixed


def load_mock_output(format_id: str, samples_dir: str | Path = "samples") -> SegCraftResponse:
    samples_path = Path(samples_dir)
    file_name = "sample_output_1.json" if format_id == "yadirect_text" else "sample_output_2.json"
    payload_path = samples_path / file_name
    if not payload_path.exists():
        raise LLMClientError(
            f"Mock файл не найден: {payload_path}. Выполните tools/sync_from_text.py."
        )
    data = json.loads(payload_path.read_text(encoding="utf-8"))
    return SegCraftResponse.model_validate(data)


def run_generation(
    prompt_text: str,
    format_id: str,
    model_name: str | None = None,
    samples_dir: str | Path = "samples",
    force_mock: bool = False,
) -> tuple[SegCraftResponse, str, str]:
    """
    Returns: (validated_response, mode, raw_text)
    mode: "mock" or "llm"
    """
    if force_mock or get_client() is None:
        return load_mock_output(format_id, samples_dir), "mock", ""

    raw_text = generate(prompt_text, model_name=model_name)
    try:
        return parse_and_validate(raw_text), "llm", raw_text
    except (json.JSONDecodeError, ValidationError, LLMValidationError) as first_error:
        repaired_raw = repair_json(raw_text, first_error, model_name=model_name)
        try:
            validated = parse_and_validate(repaired_raw)
            return validated, "llm", repaired_raw
        except (json.JSONDecodeError, ValidationError, LLMValidationError) as second_error:
            raise LLMValidationError(
                "Не удалось получить валидный JSON после repair attempt. "
                "Включите mock mode или используйте sample_output. "
                f"Причина: {second_error}"
            ) from second_error
