import os
os.environ["PYTORCH_ALLOC_CONF"] = "expandable_segments:True"

import sys
import re
import html
import tempfile

import gradio as gr
import numpy as np
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.logo_generator import generate_logo
from src.logo_prompt import build_logo_prompt
from src.brand_kit_export import export_brand_kit
from src.brand_package import build_brand_packages

COLOR_RE = re.compile(r"#[0-9A-Fa-f]{6}|#[0-9A-Fa-f]{3}")

GENERATE_LABEL = "✨ ولّد 3 اقتراحات"


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def get_brand_packages(brief: dict):
    try:
        return build_brand_packages(brief, n=3)
    except Exception as e:
        print("Brand package generation error:", e)
        return []


def _normalize_hex(hex_value: str) -> str:
    hex_value = hex_value.strip().upper()
    if hex_value.startswith("#") and len(hex_value) == 4:
        short = hex_value[1:]
        return "#" + "".join(ch * 2 for ch in short)
    return hex_value


def _extract_hex(color) -> str:
    if isinstance(color, dict):
        color = color.get("hex") or color.get("value") or color.get("code") or ""
    color_str = str(color).strip()
    match = COLOR_RE.search(color_str)
    if match:
        return _normalize_hex(match.group(0))
    return "#CCCCCC"


def _extract_color_label(color) -> str:
    if isinstance(color, dict):
        label = color.get("name") or color.get("label") or color.get("description") or ""
        return str(label).strip() or "—"

    color_str = str(color).strip()
    match = COLOR_RE.search(color_str)
    if match:
        label = color_str[match.end():].strip(" -,|;:/")
        return label or match.group(0).upper()
    return color_str or "—"


def _package_to_html(package: dict) -> str:
    brand_name = html.escape(str(package.get("brand_name") or "—"), quote=True)
    tagline = html.escape(str(package.get("tagline") or "—"), quote=True)

    raw_colors = package.get("color_palette") or []
    if isinstance(raw_colors, (str, dict)):
        raw_colors = [raw_colors]

    colors, labels = [], []
    for c in raw_colors:
        colors.append(_extract_hex(c))
        labels.append(_extract_color_label(c))

    if not colors:
        colors = ["#CCCCCC"]
        labels = ["No color"]

    swatches = ""
    for hex_code, label in zip(colors, labels):
        safe_label = html.escape(str(label), quote=True)
        swatches += (
            f"<div style='display:inline-block; width:46px; height:46px; "
            f"background:{hex_code}; border-radius:8px; margin:4px; "
            f"border:1px solid #ddd;' title='{safe_label}'></div>"
        )

    color_names = html.escape(" | ".join(str(l) for l in labels[:5]), quote=True)

    return (
        "<div style='text-align:center; padding:16px; border:1px solid #a5d6a7; "
        "border-radius:12px; background:rgba(255,255,255,0.75);'>"
        f"<h2 style='margin:0;'>{brand_name}</h2>"
        f"<p style='color:#555; font-style:italic; margin:8px 0;'>{tagline}</p>"
        f"<div>{swatches}</div>"
        f"<p style='font-size:12px; color:#777; margin-top:8px;'>{color_names}</p>"
        "</div>"
    )


def _to_pil(img):
    """يحوّل أي نوع مدخل من Gradio إلى PIL Image."""
    if img is None:
        return None

    if isinstance(img, (tuple, list)):
        img = img[0]

    if isinstance(img, dict):
        img = img.get("path") or img.get("name") or img.get("url")

    if isinstance(img, Image.Image):
        return img.convert("RGB")

    if isinstance(img, np.ndarray):
        return Image.fromarray(img).convert("RGB")

    if isinstance(img, str):
        return Image.open(img).convert("RGB")

    raise TypeError(f"نوع صورة غير مدعوم: {type(img)}")


# ------------------------------------------------------------------
# Callbacks
# ------------------------------------------------------------------
def generate_options(industry, audience, personality, tone, purpose):
    hidden = gr.update(visible=False)
    empty_card = gr.update(value="", visible=False)

    # outputs: status, packages_state, card1, card2, card3,
    #          choose1, choose2, choose3, name_btn
    if not industry or not audience:
        yield (
            "⚠️ عبّي الصناعة والجمهور المستهدف على الأقل", [],
            empty_card, empty_card, empty_card,
            hidden, hidden, hidden,
            gr.update(interactive=True, value=GENERATE_LABEL),
        )
        return

    # تعطيل الزر فوراً
    yield (
        "🧠 عم نحلّل وصف البراند ونولّد الاقتراحات... ممكن ياخد دقيقة", [],
        empty_card, empty_card, empty_card,
        hidden, hidden, hidden,
        gr.update(interactive=False, value="⏳ جاري التوليد..."),
    )

    brief = {
        "industry": industry,
        "target_audience": audience,
        "brand_purpose": purpose,
        "personality": personality,
        "tone": tone,
    }

    packages = get_brand_packages(brief)
    packages = [
        p for p in packages
        if isinstance(p, dict) and (p.get("brand_name") or p.get("tagline"))
    ]

    if not packages:
        yield (
            "❌ فشل التوليد، جرب مرة ثانية", [],
            empty_card, empty_card, empty_card,
            hidden, hidden, hidden,
            gr.update(interactive=True, value=GENERATE_LABEL),
        )
        return

    if len(packages) >= 3:
        status_text = ""
    else:
        status_text = f"⚠️ تم توليد {len(packages)} اقتراحات فقط. جرب مرة ثانية للحصول على 3."

    cards, buttons = [], []
    for i in range(3):
        if i < len(packages):
            cards.append(gr.update(value=_package_to_html(packages[i]), visible=True))
            buttons.append(gr.update(visible=True))
        else:
            cards.append(empty_card)
            buttons.append(hidden)

    yield (
        status_text, packages,
        cards[0], cards[1], cards[2],
        buttons[0], buttons[1], buttons[2],
        gr.update(interactive=True, value=GENERATE_LABEL),
    )


def choose_package(packages, index):
    """outputs: chosen_package_state, status, details_display, logo_btn, export_btn"""
    if not packages or not isinstance(packages, list) or index >= len(packages):
        return (
            None,
            "⚠️ ما في اقتراح بهذا الرقم",
            "",
            gr.update(visible=False),
            gr.update(visible=False),
        )

    chosen = packages[index]

    typography = chosen.get("typography") or "—"
    visual_style = chosen.get("visual_style") or "—"
    brand_name = chosen.get("brand_name") or "—"

    details = (
        f"**الخط المقترح:** {typography}\n\n"
        f"**الستايل البصري:** {visual_style}"
    )

    return (
        chosen,
        f"✅ اخترت: {brand_name}",
        details,
        gr.update(visible=True),
        gr.update(visible=True),
    )


def generate_logo_only(package):
    if package is None:
        yield None, "⚠️ اختاري اقتراحًا أولًا.", gr.update(interactive=True)
        return

    yield (
        None,
        "🎨 **جاري توليد اللوجو...** قد يستغرق هذا بعض الوقت، يرجى الانتظار.",
        gr.update(interactive=False),
    )

    try:
        logo_prompt = build_logo_prompt(package)
        print("LOGO PROMPT:", logo_prompt)
        logo = generate_logo(logo_prompt)

        yield (
            logo,
            "✅ تم توليد اللوجو بنجاح!",
            gr.update(interactive=True),
        )

    except Exception as e:
        print("Logo generation error:", e)
        yield (
            None,
            "❌ حدث خطأ أثناء توليد اللوجو. يمكنك المحاولة مرة أخرى.",
            gr.update(interactive=True),
        )


def export_kit(package, logo_image):
    if package is None:
        return gr.update(visible=False)

    logo_pil = _to_pil(logo_image)
    if logo_pil is None:
        return gr.update(visible=False)

    kit_image = export_brand_kit(package, logo_pil)

    pdf_path = os.path.join(tempfile.gettempdir(), "Brandora_Brand_Kit.pdf")
    kit_image.convert("RGB").save(pdf_path, "PDF", resolution=300.0)

    return gr.update(value=pdf_path, visible=True)


# ------------------------------------------------------------------
# UI
# ------------------------------------------------------------------
CUSTOM_CSS = """
.gradio-container {
    background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 45%, #a5d6a7 100%) !important;
}
#brand-title {
    text-align: center;
    margin: 10px 0 20px 0;
}
#brand-title h1 {
    font-size: 4.5rem !important;
    font-weight: 800 !important;
    background: linear-gradient(90deg, #1b5e20, #43a047, #66bb6a);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: 4px;
    margin: 0;
}
#brand-title p {
    color: #2e7d32;
    font-size: 1.2rem;
}
"""

with gr.Blocks(
    theme=gr.themes.Soft(primary_hue="green", secondary_hue="emerald"),
    css=CUSTOM_CSS,
    title="Brandora",
) as demo:
    gr.Markdown(
        """
        # ✦ Brandora ✦
        مولّد الهوية البصرية بالذكاء الاصطناعي
        """,
        elem_id="brand-title",
    )

    packages_state = gr.State([])
    chosen_package_state = gr.State(None)

    gr.Markdown("#### وصف البراند")

    with gr.Row():
        industry = gr.Textbox(label="الصناعة", placeholder="مثال: coffee shop")
        audience = gr.Textbox(label="الجمهور المستهدف", placeholder="مثال: university students")

    with gr.Row():
        purpose = gr.Textbox(
            label="هدف البراند",
            placeholder="مثال: مكان مريح للدراسة والتجمع",
        )
        personality = gr.CheckboxGroup(
            choices=["modern", "playful", "elegant", "bold", "warm", "minimalist",
                     "energetic", "trustworthy", "luxurious", "friendly", "rebellious", "calm"],
            label="الشخصية (اختار أكتر من وحدة)",
        )
        tone = gr.Dropdown(
            choices=["casual", "formal", "playful", "sophisticated", "friendly", "bold"],
            label="النبرة",
            value="casual",
        )

    name_btn = gr.Button(GENERATE_LABEL, variant="primary", size="lg")

    status = gr.Markdown()

    gr.Markdown("#### اختار الاقتراح اللي عجبك")

    with gr.Row():
        with gr.Column():
            card1 = gr.HTML(visible=False)
            choose1 = gr.Button("اختار هذا ✓", visible=False)
        with gr.Column():
            card2 = gr.HTML(visible=False)
            choose2 = gr.Button("اختار هذا ✓", visible=False)
        with gr.Column():
            card3 = gr.HTML(visible=False)
            choose3 = gr.Button("اختار هذا ✓", visible=False)

    gr.Markdown("#### النتيجة النهائية")

    details_display = gr.Markdown()

    logo_btn = gr.Button("🖼️ ولّد اللوجو", variant="secondary", visible=False)
    logo_status = gr.Markdown()

    logo_display = gr.Image(
        label="اللوجو",
        height=300,
        interactive=False,
        type="pil",
    )
    export_btn = gr.Button("📦 حمّل Brand Kit", variant="secondary", visible=False)
    export_file = gr.File(label="📄 تحميل Brand Kit PDF", visible=False)

    gr.Examples(
        examples=[
            [
                "coffee",
                "university students",
                "provide a comfortable place for studying and socializing",
                ["friendly"],
                "friendly",
            ],
            [
                "streetwear",
                "Gen Z urban creatives",
                "express individuality through bold designs",
                ["bold"],
                "bold",
            ],
        ],
        inputs=[industry, audience, purpose, personality, tone],
    )

    # ---------------- Events ----------------
    name_btn.click(
        fn=generate_options,
        inputs=[industry, audience, personality, tone, purpose],
        outputs=[
            status, packages_state,
            card1, card2, card3,
            choose1, choose2, choose3,
            name_btn,
        ],
        concurrency_limit=1,
    )

    choose1.click(fn=lambda pkgs: choose_package(pkgs, 0), inputs=[packages_state],
                  outputs=[chosen_package_state, status, details_display, logo_btn, export_btn])
    choose2.click(fn=lambda pkgs: choose_package(pkgs, 1), inputs=[packages_state],
                  outputs=[chosen_package_state, status, details_display, logo_btn, export_btn])
    choose3.click(fn=lambda pkgs: choose_package(pkgs, 2), inputs=[packages_state],
                  outputs=[chosen_package_state, status, details_display, logo_btn, export_btn])

    logo_btn.click(
        fn=generate_logo_only,
        inputs=[chosen_package_state],
        outputs=[logo_display, logo_status, logo_btn],
        concurrency_limit=1,
    )

    export_btn.click(
        fn=export_kit,
        inputs=[chosen_package_state, logo_display],
        outputs=export_file,
    )

if __name__ == "__main__":
    demo.queue().launch(share=True)