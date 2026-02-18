# SegCraft

SegCraft — MVP AI-редактора массовых вариаций рекламных текстов под сегменты аудитории.

Ключевая идея: не чат-бот, а конвейер с фиксированной структурой результата, библиотекой сегментов, risk-метками и экспортом в рабочие форматы.

## Что внутри

- `app.py` — Streamlit UI (ввод, параметры, генерация, табличный вывод, экспорт)
- `llm_client.py` — вызов LLM, mock mode, JSON repair, валидация
- `prompt_builder.py` — сбор case bundle промпта
- `schemas.py` — Pydantic-схемы structured output
- `tools/sync_from_text.py` — генерация всех контентных файлов из `input_texts/text.txt`
- `tools/generate_mock_images.py` — генерация PNG-моков для презентации
- `deck/make_deck.js` — сборка PPTX через PptxGenJS
- `submission/answers.md` — ответы на задания для отправки
- `submission/demo_script.md` — сценарий демо на 3–4 минуты
- `submission/pitch_1pager.md` — одностраничный питч

## Единый источник контента

Все смысловые материалы берутся из `input_texts/text.txt`.

Из этого файла автоматически собираются:
- `segments/default_segments_ru.json`
- `formats/ad_formats_ru.json`
- `samples/sample_input_*.txt`
- `samples/sample_output_*.json`
- `submission/demo_script.md`
- `submission/answers.md`
- `submission/pitch_1pager.md`
- `deck/deck_config.json`

Если в `input_texts/text.txt` не хватает обязательных секций, `tools/sync_from_text.py` завершится с понятной ошибкой и подсказкой по секциям.

## Установка

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Подготовка контента

```bash
python tools/sync_from_text.py
```

## Запуск MVP

```bash
streamlit run app.py
```

## Переменные окружения

Скопируйте `.env.example` в `.env` и заполните:

```env
OPENAI_API_KEY=...
MODEL_NAME=gpt-4o-mini
```

## Mock mode

Если `OPENAI_API_KEY` не задан:
- генерация работает в mock mode,
- автоматически используется `samples/sample_output_1.json` (для `yadirect_text`) или `samples/sample_output_2.json` (для остальных форматов),
- UI и экспорт работают полностью.

## Генерация презентации

1. Сгенерировать PNG-моки:
```bash
python tools/generate_mock_images.py
```

2. Установить зависимость и собрать PPTX:
```bash
npm install pptxgenjs
node deck/make_deck.js
```

Итоговый файл:
- `deck/segcraft_yandex_style.pptx`

## Материалы для отправки

- Ответы: `submission/answers.md`
- Сценарий демо: `submission/demo_script.md`
- Одностраничник: `submission/pitch_1pager.md`

## Acceptance checklist

- [x] `streamlit run app.py` (при установленных зависимостях)
- [x] mock mode без API ключа
- [x] structured JSON + валидация и repair attempt
- [x] матрица сегментов и экспорт CSV/JSON
- [x] генерация конфигурации презентации и ассетов
