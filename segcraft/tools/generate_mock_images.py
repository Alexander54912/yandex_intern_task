#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as exc:  # pragma: no cover
    print("[images:error] Pillow не установлен. Установите зависимости из requirements.txt.")
    raise SystemExit(1) from exc

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ASSETS_DIR = PROJECT_ROOT / "deck" / "assets"

WIDTH = 1600
HEIGHT = 900
WHITE = (255, 255, 255)
BLACK = (24, 24, 24)
GRAY = (230, 230, 230)
RED = (255, 58, 58)


def get_font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("Arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def draw_panel(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, title: str) -> None:
    draw.rectangle((x, y, x + w, y + h), outline=GRAY, width=3)
    draw.text((x + 18, y + 14), title, fill=BLACK, font=get_font(24))


def create_ui_mock_1(path: Path) -> None:
    image = Image.new("RGB", (WIDTH, HEIGHT), WHITE)
    draw = ImageDraw.Draw(image)

    draw.rectangle((0, 0, WIDTH, 18), fill=RED)
    draw.text((36, 44), "SegCraft UI: Input + Parameters", fill=BLACK, font=get_font(42))

    draw_panel(draw, 40, 120, 920, 730, "Ввод")
    draw_panel(draw, 1000, 120, 560, 730, "Параметры")

    blocks = [
        (70, 180, 860, 150, "Базовый текст / оффер"),
        (70, 360, 860, 120, "Контекст продукта"),
        (70, 510, 860, 110, "Добавить свой сегмент"),
        (70, 650, 860, 170, "Ограничения и запреты"),
    ]
    for x, y, w, h, label in blocks:
        draw.rectangle((x, y, x + w, y + h), outline=GRAY, width=2)
        draw.text((x + 12, y + 12), label, fill=(80, 80, 80), font=get_font(24))

    right_lines = [
        "[x] Новичок SMB",
        "[x] Цена-чувствительные",
        "[x] Локальный офлайн",
        "[x] Скептик",
        "Тон: нейтральный",
        "Формат: Яндекс Директ",
        "Варианты: 2",
        "Вариативность: средне",
        "Mock mode: ON",
    ]
    y = 190
    for line in right_lines:
        draw.text((1030, y), line, fill=BLACK, font=get_font(26))
        y += 62

    draw.rounded_rectangle((1080, 760, 1500, 832), radius=18, fill=RED)
    draw.text((1130, 778), "Сгенерировать пакет", fill=WHITE, font=get_font(30))

    image.save(path)


def create_ui_mock_2(path: Path) -> None:
    image = Image.new("RGB", (WIDTH, HEIGHT), WHITE)
    draw = ImageDraw.Draw(image)

    draw.rectangle((0, 0, WIDTH, 18), fill=RED)
    draw.text((36, 44), "SegCraft UI: Results", fill=BLACK, font=get_font(42))

    draw.rectangle((40, 120, 1560, 190), outline=GRAY, width=2)
    tabs = ["Summary", "Matrix", "Differences", "Questions", "JSON", "Export"]
    x = 70
    for tab in tabs:
        fill = RED if tab == "Matrix" else WHITE
        color = WHITE if tab == "Matrix" else BLACK
        draw.rounded_rectangle((x, 132, x + 210, 178), radius=14, fill=fill, outline=GRAY)
        draw.text((x + 26, 145), tab, fill=color, font=get_font(24))
        x += 240

    draw.rectangle((40, 220, 1560, 840), outline=GRAY, width=3)
    draw.text((70, 250), "Матрица вариаций по сегментам", fill=BLACK, font=get_font(32))

    rows = [
        "Новичок SMB | Простой старт | Вариант #1 | Вариант #2 | CTA | риски | 41/78",
        "Цена-чувств. | Прозрачность | Вариант #1 | Вариант #2 | CTA | риски | 39/75",
        "Локальный офф. | Клиенты рядом | Вариант #1 | Вариант #2 | CTA | - | 44/77",
        "Скептик | Контроль шага | Вариант #1 | Вариант #2 | CTA | risks | 43/79",
    ]
    y = 310
    for row in rows:
        draw.rectangle((70, y - 12, 1530, y + 48), outline=GRAY, width=1)
        draw.text((80, y), row, fill=BLACK, font=get_font(20))
        y += 90

    draw.rounded_rectangle((70, 770, 320, 830), radius=12, fill=RED)
    draw.text((105, 788), "Скачать CSV", fill=WHITE, font=get_font(24))
    draw.rounded_rectangle((350, 770, 620, 830), radius=12, fill=BLACK)
    draw.text((395, 788), "Скачать JSON", fill=WHITE, font=get_font(24))

    image.save(path)


def create_table_mock(path: Path) -> None:
    image = Image.new("RGB", (WIDTH, HEIGHT), WHITE)
    draw = ImageDraw.Draw(image)

    draw.rectangle((0, 0, WIDTH, 14), fill=RED)
    draw.text((48, 34), "Result Matrix Snapshot", fill=BLACK, font=get_font(42))

    x0, y0 = 40, 120
    cols = [280, 220, 280, 280, 150, 260, 170]
    headers = [
        "Сегмент",
        "Триггер",
        "Вариант #1",
        "Вариант #2",
        "CTA",
        "Risk-метки",
        "Символы",
    ]

    x = x0
    for width, header in zip(cols, headers):
        draw.rectangle((x, y0, x + width, y0 + 64), fill=(248, 248, 248), outline=GRAY, width=2)
        draw.text((x + 10, y0 + 20), header, fill=BLACK, font=get_font(22))
        x += width

    sample_rows = [
        [
            "Новичок SMB",
            "Простой старт",
            "Без сложных\nнастроек",
            "Первые показы\nс планом",
            "Попробовать",
            "-",
            "42/79; 41/76",
        ],
        [
            "Скептик",
            "Контроль",
            "Снова, но\nуправляемо",
            "Тест на\nмалом объёме",
            "Разобрать",
            "vague_offer",
            "45/80; 43/78",
        ],
    ]

    y = y0 + 64
    for row in sample_rows:
        x = x0
        for width, cell in zip(cols, row):
            draw.rectangle((x, y, x + width, y + 120), outline=GRAY, width=1)
            draw.text((x + 10, y + 18), cell, fill=BLACK, font=get_font(20))
            x += width
        y += 120

    image.save(path)


def create_flow_diagram(path: Path) -> None:
    image = Image.new("RGB", (WIDTH, HEIGHT), WHITE)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, WIDTH, 16), fill=RED)
    draw.text((36, 40), "SegCraft Flow", fill=BLACK, font=get_font(44))

    boxes = [
        (80, 320, 260, 150, "Input\nOffer + Segments"),
        (430, 320, 260, 150, "Prompt\nBuilder"),
        (780, 320, 260, 150, "LLM\nStructured JSON"),
        (1130, 320, 260, 150, "Matrix + Export\nCSV/JSON"),
    ]

    for x, y, w, h, label in boxes:
        draw.rounded_rectangle((x, y, x + w, y + h), radius=20, outline=BLACK, width=4)
        draw.text((x + 24, y + 50), label, fill=BLACK, font=get_font(28))

    for i in range(len(boxes) - 1):
        x1 = boxes[i][0] + boxes[i][2]
        y1 = boxes[i][1] + boxes[i][3] // 2
        x2 = boxes[i + 1][0]
        draw.line((x1 + 8, y1, x2 - 12, y1), fill=RED, width=8)
        draw.polygon(
            [(x2 - 12, y1), (x2 - 34, y1 - 14), (x2 - 34, y1 + 14)],
            fill=RED,
        )

    draw.text((520, 580), "Risk flags + Validation + Repair", fill=BLACK, font=get_font(32))
    draw.rectangle((500, 628, 1090, 690), outline=RED, width=4)
    draw.text((530, 646), "mock mode fallback when no API key", fill=BLACK, font=get_font(24))

    image.save(path)


def main() -> None:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    create_ui_mock_1(ASSETS_DIR / "ui_mock_1.png")
    create_ui_mock_2(ASSETS_DIR / "ui_mock_2.png")
    create_table_mock(ASSETS_DIR / "table_mock.png")
    create_flow_diagram(ASSETS_DIR / "flow_diagram.png")
    print("[images] Created deck mock assets in deck/assets/")


if __name__ == "__main__":
    main()
