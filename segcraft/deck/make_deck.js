const fs = require("fs");
const path = require("path");

let PptxGenJS;
try {
  PptxGenJS = require("pptxgenjs");
} catch (err) {
  console.error("[deck:error] Missing dependency: pptxgenjs. Install with: npm install pptxgenjs");
  process.exit(1);
}

const deckDir = __dirname;
const configPath = path.join(deckDir, "deck_config.json");
const outputPath = path.join(deckDir, "segcraft_yandex_style.pptx");

if (!fs.existsSync(configPath)) {
  console.error("[deck:error] deck_config.json not found. Run python tools/sync_from_text.py first.");
  process.exit(1);
}

const config = JSON.parse(fs.readFileSync(configPath, "utf-8"));
const style = config.style || {};
const slides = config.slides || [];

const pptx = new PptxGenJS();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "SegCraft MVP";
pptx.subject = "Segmented Ad Copy Pipeline";
pptx.company = "SegCraft";
pptx.title = `${config.project?.name || "SegCraft"} deck`;
pptx.lang = "ru-RU";
pptx.theme = {
  headFontFace: style.title_font || "Arial",
  bodyFontFace: style.body_font || "Arial",
  lang: "ru-RU",
};

const bgColor = style.bg_color || "FFFFFF";
const textColor = style.text_color || "111111";
const accentColor = style.accent_color || "FF3333";

slides.forEach((slideData) => {
  const slide = pptx.addSlide();

  slide.background = { color: bgColor };
  slide.addShape(pptx.ShapeType.rect, {
    x: 0,
    y: 0,
    w: 13.333,
    h: 0.09,
    fill: { color: accentColor },
    line: { color: accentColor },
  });

  slide.addText(slideData.title || "", {
    x: 0.55,
    y: 0.35,
    w: 8.8,
    h: 0.8,
    fontFace: style.title_font || "Arial",
    fontSize: 34,
    bold: true,
    color: textColor,
    valign: "mid",
  });

  const bullets = Array.isArray(slideData.bullets) ? slideData.bullets : [];
  const bulletTextRuns = [];
  bullets.forEach((item) => {
    bulletTextRuns.push({ text: `• ${item}\n`, options: { breakLine: true } });
  });
  if (bulletTextRuns.length > 0) {
    slide.addText(bulletTextRuns, {
      x: 0.7,
      y: 1.45,
      w: 6.1,
      h: 4.9,
      fontFace: style.body_font || "Arial",
      fontSize: 19,
      color: textColor,
      valign: "top",
      margin: 1,
      lineSpacingMultiple: 1.1,
    });
  }

  if (slideData.image) {
    const imagePath = path.join(deckDir, slideData.image);
    if (fs.existsSync(imagePath)) {
      slide.addImage({ path: imagePath, x: 6.95, y: 1.35, w: 5.95, h: 4.55 });
    }
  }

  slide.addText(`${slideData.number || ""}`, {
    x: 12.4,
    y: 6.95,
    w: 0.5,
    h: 0.2,
    fontFace: style.body_font || "Arial",
    fontSize: 11,
    color: "666666",
    align: "right",
  });

  if (slideData.notes) {
    slide.addNotes(slideData.notes);
  }
});

pptx
  .writeFile({ fileName: outputPath })
  .then(() => {
    console.log(`[deck] Generated: ${outputPath}`);
  })
  .catch((err) => {
    console.error("[deck:error] Failed to generate PPTX", err);
    process.exit(1);
  });
