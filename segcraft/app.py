from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from content_source import parse_key_values, parse_sections, read_text_source
from llm_client import LLMClientError, LLMValidationError, load_mock_output, run_generation
from prompt_builder import build_case_bundle
from schemas import SegCraftResponse

PROJECT_ROOT = Path(__file__).resolve().parent
INPUT_TEXT_PATH = PROJECT_ROOT / "input_texts" / "text.txt"
SEGMENTS_PATH = PROJECT_ROOT / "segments" / "default_segments_ru.json"
FORMATS_PATH = PROJECT_ROOT / "formats" / "ad_formats_ru.json"
SAMPLE_INPUT_1_PATH = PROJECT_ROOT / "samples" / "sample_input_1_ru.txt"
SAMPLE_INPUT_2_PATH = PROJECT_ROOT / "samples" / "sample_input_2_ru.txt"

P0_RISK_TYPES = {"forbidden_claims", "compliance_sensitive", "format_overflow"}


@st.cache_data(show_spinner=False)
def load_json_file(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(
            f"Не найден файл: {path}. Выполните python tools/sync_from_text.py из каталога segcraft/."
        )
    return json.loads(path.read_text(encoding="utf-8"))


@st.cache_data(show_spinner=False)
def load_content_defaults() -> dict[str, Any]:
    raw_text = read_text_source(INPUT_TEXT_PATH)
    sections = parse_sections(raw_text)

    constraints_map = parse_key_values(sections.get("CONSTRAINTS_LIBRARY", ""))
    constraints = [value for _, value in sorted(constraints_map.items())]

    sample_1 = parse_key_values(SAMPLE_INPUT_1_PATH.read_text(encoding="utf-8"))
    sample_2 = parse_key_values(SAMPLE_INPUT_2_PATH.read_text(encoding="utf-8"))

    return {
        "constraints": constraints,
        "sample_1": sample_1,
        "sample_2": sample_2,
    }


def parse_constraints(raw_text: str) -> list[str]:
    normalized = raw_text.replace(";", "\n")
    return [line.strip() for line in normalized.splitlines() if line.strip()]


def build_matrix(response: SegCraftResponse, p0_only: bool = False) -> pd.DataFrame:
    rows: list[dict[str, str]] = []

    for segment in response.segments:
        row: dict[str, str] = {
            "Сегмент": segment.segment_name,
            "Триггер": segment.trigger,
        }

        cta_values: list[str] = []
        risk_values: list[str] = []
        chars_values: list[str] = []

        for index, copy in enumerate(segment.copies, start=1):
            row[f"Вариант #{index}"] = f"{copy.headline}\n{copy.body}"
            cta_values.append(copy.cta)
            chars_values.append(
                f"v{index}: {copy.char_count.headline}/{copy.char_count.body}"
            )

            for risk in copy.risk_flags:
                if p0_only and risk.type not in P0_RISK_TYPES:
                    continue
                risk_values.append(f"{risk.type}: {risk.note}")

        row["CTA"] = " | ".join(cta_values)
        row["Risk-метки"] = " ; ".join(risk_values) if risk_values else "-"
        row["Символы (headline/body)"] = " ; ".join(chars_values)
        rows.append(row)

    return pd.DataFrame(rows)


def to_markdown_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "| Пусто |\n|---|\n| Нет данных |"
    return frame.to_markdown(index=False)


def segment_label(segment: dict[str, Any]) -> str:
    return f"{segment['name']} ({segment['segment_id']})"


def create_custom_segment(text: str) -> dict[str, Any]:
    short_name = text.strip().split(".")[0][:48] if text.strip() else "Пользовательский сегмент"
    return {
        "segment_id": "custom_segment",
        "name": short_name,
        "who": text.strip(),
        "job_to_be_done": text.strip(),
        "pains": [],
        "triggers": ["Актуально из пользовательского ввода"],
        "taboos": [],
        "tone_hint": "По контексту пользовательского сегмента",
        "cta_style": "Нейтральный",
        "example_offer_adaptations": [],
    }


def render_result(response: SegCraftResponse, mode: str, p0_only: bool) -> None:
    tabs = st.tabs(["Summary", "Matrix", "Differences", "Questions", "JSON", "Export"])
    matrix_df = build_matrix(response, p0_only=p0_only)

    with tabs[0]:
        st.subheader("Executive Summary")
        st.write(response.exec_summary.for_marketer)
        st.write(response.exec_summary.for_non_tech_manager)
        st.caption(f"Режим генерации: {mode}")

        if response.global_risks:
            st.markdown("**Global Risks**")
            for risk in response.global_risks:
                st.write(f"- {risk.risk}: {risk.impact} | Митигация: {risk.mitigation}")

    with tabs[1]:
        st.subheader("Матрица вариантов")
        st.dataframe(matrix_df, use_container_width=True)

    with tabs[2]:
        st.subheader("Чем варианты отличаются")
        for segment in response.segments:
            st.markdown(f"**{segment.segment_name}**")
            st.write(segment.differences_note)
            st.caption(f"Угол: {segment.angle}")

    with tabs[3]:
        st.subheader("Уточняющие вопросы")
        if response.questions:
            q_df = pd.DataFrame([q.model_dump() for q in response.questions])
            st.dataframe(q_df, use_container_width=True)
        else:
            st.info("Уточняющих вопросов нет.")

    with tabs[4]:
        st.subheader("JSON")
        st.json(response.model_dump(mode="json"))

    with tabs[5]:
        st.subheader("Export")
        csv_bytes = matrix_df.to_csv(index=False).encode("utf-8-sig")
        json_bytes = response.model_dump_json(indent=2).encode("utf-8")
        st.download_button(
            label="Скачать CSV",
            data=csv_bytes,
            file_name="segcraft_matrix.csv",
            mime="text/csv",
        )
        st.download_button(
            label="Скачать JSON",
            data=json_bytes,
            file_name="segcraft_result.json",
            mime="application/json",
        )

        st.markdown("**Копировать таблицу в буфер**")
        st.caption("Скопируйте Markdown-таблицу ниже.")
        st.code(to_markdown_table(matrix_df), language="markdown")

        team_message = (
            "Вот пакет вариаций под сегменты. Предлагаю выбрать по 1-2 варианта на сегмент "
            "и запустить первую волну теста."
        )
        st.markdown("**Сообщение в командный чат**")
        st.code(team_message)


def main() -> None:
    load_dotenv()
    st.set_page_config(page_title="SegCraft MVP", layout="wide")
    st.title("SegCraft — AI-редактор массовых вариаций под сегменты аудитории")

    try:
        segments: list[dict[str, Any]] = load_json_file(SEGMENTS_PATH)
        formats: list[dict[str, Any]] = load_json_file(FORMATS_PATH)
        defaults = load_content_defaults()
    except Exception as exc:
        st.error(str(exc))
        st.stop()

    sample_1 = defaults["sample_1"]
    constraint_defaults = defaults["constraints"]
    selected_sample = st.radio(
        "Стартовый пример",
        options=["SAMPLE_INPUT_1", "SAMPLE_INPUT_2"],
        horizontal=True,
    )

    active_sample = sample_1 if selected_sample == "SAMPLE_INPUT_1" else defaults["sample_2"]
    default_segment_ids = set(
        item.strip()
        for item in active_sample.get("selected_segments", "").split(";")
        if item.strip()
    )

    left_col, right_col = st.columns([1.35, 1])

    with left_col:
        base_text = st.text_area(
            "Базовый текст / оффер",
            value=active_sample.get("base_text", ""),
            height=170,
            help="Обязательное поле",
        )

        product_context = st.text_area(
            "Контекст продукта",
            value=active_sample.get("product_context", ""),
            height=120,
            help="Опционально: продукт, ЦА, платформа, особенности",
        )

        custom_segment_text = st.text_area(
            "Добавить свой сегмент текстом (опционально)",
            value="",
            height=80,
        )

        constraints_text = st.text_area(
            "Ограничения и запреты",
            value="\n".join(constraint_defaults),
            height=130,
            help="Можно писать с новой строки или через ';'",
        )

    with right_col:
        st.markdown("### Параметры")
        st.markdown("**Сегменты аудитории (выберите >= 3)**")

        checked_segment_ids: list[str] = []
        for segment in segments:
            is_checked = st.checkbox(
                segment_label(segment),
                value=segment["segment_id"] in default_segment_ids,
                key=f"{selected_sample}_{segment['segment_id']}",
            )
            if is_checked:
                checked_segment_ids.append(segment["segment_id"])

        tone_label_to_value = {
            "дружелюбный": "friendly",
            "нейтральный": "neutral",
            "официальный": "formal",
            "дерзкий": "bold",
        }
        tone_label = st.selectbox(
            "Тон/стиль",
            options=list(tone_label_to_value.keys()),
            index=1,
        )

        language = st.selectbox("Язык", options=["RU"], index=0)

        format_option_labels = [
            f"{fmt['name']} | h≤{fmt['limits']['headline_max']} / b≤{fmt['limits']['body_max']}"
            for fmt in formats
        ]
        default_format_idx = next(
            (
                index
                for index, fmt in enumerate(formats)
                if fmt["format_id"] == active_sample.get("format_id")
            ),
            0,
        )
        format_label = st.selectbox("Формат", options=format_option_labels, index=default_format_idx)
        selected_format = formats[format_option_labels.index(format_label)]

        variants_per_segment = st.slider(
            "Количество вариантов на сегмент",
            min_value=1,
            max_value=3,
            value=int(active_sample.get("variants_per_segment", "2")),
        )

        variability_map = {
            "мягко (сохранить смысл близко)": "soft",
            "средне": "medium",
            "смело (новые углы)": "bold",
        }
        default_variability = active_sample.get("variability_level", "medium")
        default_variability_label = next(
            (label for label, value in variability_map.items() if value == default_variability),
            "средне",
        )
        variability_label = st.selectbox(
            "Уровень вариативности",
            options=list(variability_map.keys()),
            index=list(variability_map.keys()).index(default_variability_label),
        )

        has_api_key = bool(os.getenv("OPENAI_API_KEY", "").strip())
        force_mock = st.checkbox("Mock mode", value=not has_api_key)
        p0_only = st.checkbox("P0 risks only", value=False)

    if st.button("Сгенерировать пакет", type="primary"):
        if not base_text.strip():
            st.error("Поле 'Базовый текст / оффер' обязательно.")
            st.stop()

        selected_segments = [
            segment for segment in segments if segment["segment_id"] in checked_segment_ids
        ]
        if len(selected_segments) < 3:
            st.error("Выберите минимум 3 сегмента аудитории.")
            st.stop()

        if custom_segment_text.strip():
            selected_segments.append(create_custom_segment(custom_segment_text))

        constraints = parse_constraints(constraints_text)
        tone_value = tone_label_to_value[tone_label]
        variability_value = variability_map[variability_label]

        prompt_text = build_case_bundle(
            base_text=base_text.strip(),
            context=product_context.strip(),
            selected_segments=selected_segments,
            format_spec=selected_format,
            constraints=constraints,
            tone=tone_value,
            language=language,
            variants_per_segment=variants_per_segment,
            variability_level=variability_value,
        )

        with st.spinner("Генерирую пакет..."):
            try:
                response, mode, _ = run_generation(
                    prompt_text=prompt_text,
                    format_id=selected_format["format_id"],
                    samples_dir=PROJECT_ROOT / "samples",
                    force_mock=force_mock,
                )
            except (LLMValidationError, LLMClientError) as exc:
                st.error(str(exc))
                st.warning("Показываю sample_output как fallback. Для реального запроса включите API ключ.")
                response = load_mock_output(
                    format_id=selected_format["format_id"],
                    samples_dir=PROJECT_ROOT / "samples",
                )
                mode = "mock-fallback"

        if len(response.segments) != len(selected_segments):
            st.warning(
                "Число сегментов в ответе не совпало с выбором. Проверьте качество входа или повторите генерацию."
            )

        render_result(response=response, mode=mode, p0_only=p0_only)


if __name__ == "__main__":
    main()
