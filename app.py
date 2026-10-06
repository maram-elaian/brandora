import gradio as gr

import sys
import os
import re
import html
import tempfile


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.logo_generator import generate_logo
from src.logo_prompt import build_logo_prompt
from src.brand_kit_export import export_brand_kit
from src.brand_package import build_brand_packages

COLOR_RE = re.compile(r"#[0-9A-Fa-f]{6}|#[0-9A-Fa-f]{3}")


def get_brand_packages(brief: dict):
    try:
        return build_brand_packages(brief, n=3)
    except Exception as e:
        print("Brand package generation error:", e)
        return []


def _empty_ui(status_text: str = ""):
    """
    يرجع 8 outputs مطابقة لـ generate_options:
    status, packages_state, card1, card2, card3, choose1, choose2, choose3
    """
    return (
        status_text,
        [],
        gr.update(value="", visible=False),
        gr.update(value="", visible=False),
        gr.update(value="", visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
    )


def _normalize_hex(hex_value: str) -> str:
    """
    يحول #abc إلى #AABBCC
    ويحافظ على #AABBCC
    """
    hex_value = hex_value.strip().upper()

    if hex_value.startswith("#") and len(hex_value) == 4:
        short = hex_value[1:]
        return "#" + "".join(ch * 2 for ch in short)

    return hex_value


def _extract_hex(color) -> str:
    """
    يستخرج لون hex من:
    - "#8B5A2B warm terracotta"
    - "#8B5A2B"
    - {"hex": "#8B5A2B", "name": "warm terracotta"}
    """
    if isinstance(color, dict):
        color = (
            color.get("hex")
            or color.get("value")
            or color.get("code")
            or ""
        )

    color_str = str(color).strip()
    match = COLOR_RE.search(color_str)

    if match:
        return _normalize_hex(match.group(0))

    return "#CCCCCC"


def _extract_color_label(color) -> str:
    """
    يستخرج اسم اللون أو وصفه:
    - "#8B5A2B warm terracotta" → "warm terracotta"
    - {"hex": "#8B5A2B", "name": "warm terracotta"} → "warm terracotta"
    """
    if isinstance(color, dict):
        label = (
            color.get("name")
            or color.get("label")
            or color.get("description")
            or ""
        )
        return str(label).strip() or "—"

    color_str = str(color).strip()
    match = COLOR_RE.search(color_str)

    if match:
        label = color_str[match.end():].strip(" -,|;:/")
        return label or match.group(0).upper()

    return color_str or "—"


def _package_to_html(package: dict) -> str:
    """
    يبني بطاقة HTML للاقتراح.
    """
    brand_name = html.escape(str(package.get("brand_name") or "—"), quote=True)
    tagline = html.escape(str(package.get("tagline") or "—"), quote=True)

    raw_colors = package.get("color_palette") or []

    if isinstance(raw_colors, str):
        raw_colors = [raw_colors]

    if isinstance(raw_colors, dict):
        raw_colors = [raw_colors]

    colors = []
    labels = []

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

    color_names = " | ".join(str(label) for label in labels[:5])
    color_names = html.escape(color_names, quote=True)

    return (
        "<div style='text-align:center; padding:16px; border:1px solid #e0e0e0; border-radius:12px;'>"
        f"<h2 style='margin:0;'>{brand_name}</h2>"
        f"<p style='color:#666; font-style:italic; margin:8px 0;'>{tagline}</p>"
        f"<div>{swatches}</div>"
        f"<p style='font-size:12px; color:#888; margin-top:8px;'>{color_names}</p>"
        "</div>"
    )


import time

LOADING_MESSAGES = [
    "🧠 عم نحلّل وصف البراند...",
    "✨ عم نولّد أسماء إبداعية...",
    "🎨 عم نختار الألوان المناسبة...",
]


def generate_options(industry, audience, personality, tone, purpose):
    if not industry or not audience:
        yield "⚠️ عبّي الصناعة والجمهور المستهدف على الأقل", [], \
              gr.update(value="", visible=False), gr.update(value="", visible=False), gr.update(value="", visible=False), \
              gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)
        return

    for msg in LOADING_MESSAGES:
        yield msg, [], \
              gr.update(value="", visible=False), gr.update(value="", visible=False), gr.update(value="", visible=False), \
              gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)
        time.sleep(1)

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
        yield "❌ فشل التوليد، جربي مرة ثانية", [], \
              gr.update(value="", visible=False), gr.update(value="", visible=False), gr.update(value="", visible=False), \
              gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)
        return

    if len(packages) >= 3:
        status = ""
    else:
        status = f"⚠️ تم توليد {len(packages)} اقتراحات فقط. جربي مرة ثانية للحصول على 3."

    cards = []
    buttons = []
    for i in range(3):
        if i < len(packages):
            cards.append(gr.update(value=_package_to_html(packages[i]), visible=True))
            buttons.append(gr.update(visible=True))
        else:
            cards.append(gr.update(value="", visible=False))
            buttons.append(gr.update(visible=False))

    yield status, packages, cards[0], cards[1], cards[2], buttons[0], buttons[1], buttons[2]


def choose_package(packages, index):
    """
    يختار الاقتراح رقم index من packages.

    outputs:
    chosen_package_state, status, details_display, logo_btn
    """
    if not packages or not isinstance(packages, list) or index >= len(packages):
        return (
            None,
            "⚠️ ما في اقتراح بهذا الرقم",
            "",
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

    # أثناء الانتظار:
    # - نمسح الصورة القديمة
    # - نظهر رسالة للمستخدم
    # - نعطّل الزر لمنع الضغط مرة ثانية
    yield (
        None,
        "🎨 **جاري توليد اللوجو...** قد يستغرق هذا بعض الوقت، يرجى الانتظار.",
        gr.update(interactive=False)
    )

    try:
        logo_prompt = build_logo_prompt(package)
        logo = generate_logo(logo_prompt)

        # بعد انتهاء FLUX:
        # - نعرض اللوجو
        # - نزيل رسالة الانتظار
        # - نعيد تفعيل الزر
        yield (
            logo,
            "✅ تم توليد اللوجو بنجاح!",
            gr.update(interactive=True)
        )

    except Exception as e:
        print("Logo generation error:", e)

        # في حالة الخطأ، نعيد تفعيل الزر
        yield (
            None,
            "❌ حدث خطأ أثناء توليد اللوجو. يمكنك المحاولة مرة أخرى.",
            gr.update(interactive=True)
        )


def export_kit(package, logo_image):
    if package is None:
        return None

    kit_image = export_brand_kit(package, logo_image)

    pdf_path = os.path.join(
        tempfile.gettempdir(),
        "Brandora_Brand_Kit.pdf"
    )

    kit_image.save(
        pdf_path,
        "PDF",
        resolution=300.0
    )

    return pdf_path

with gr.Blocks(
    theme=gr.themes.Soft(primary_hue="violet"),
    title="Brandora"
) as demo:
    gr.Markdown(
        """
        #  ✦. ⊹ ˚ .꒰ Brandora ꒱ ‧₊˚★
        ### مولّد الهوية البصرية بالذكاء الاصطناعي
        """
    )

    packages_state = gr.State([])
    chosen_package_state = gr.State(None)

    gr.Markdown("#### وصف البراند")

    with gr.Row():
        industry = gr.Textbox(
            label="الصناعة",
            placeholder="مثال: coffee shop"
        )
        audience = gr.Textbox(
            label="الجمهور المستهدف",
            placeholder="مثال: university students"
        )

    with gr.Row():
        purpose = gr.Textbox(
            label="هدف البراند",
            placeholder="مثال: مكان مريح للدراسة والتجمع"
        )
        personality = gr.CheckboxGroup(
            choices=["modern", "playful", "elegant", "bold", "warm", "minimalist",
                     "energetic", "trustworthy", "luxurious", "friendly", "rebellious", "calm"],
            label="الشخصية (اختار أكتر من وحدة)",
        )
        tone = gr.Dropdown(
            choices=["casual", "formal", "playful", "sophisticated", "friendly", "bold"],
            label="النبرة", value="casual",
        )

    name_btn = gr.Button(
        "✨ ولّد 3 اقتراحات",
        variant="primary",
        size="lg"
    )

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

    logo_btn = gr.Button(
        "🖼️ ولّد اللوجو",
        variant="secondary",
        visible=False
    )

    logo_status = gr.Markdown()



    logo_display = gr.Image(label="اللوجو", height=300, interactive=False)
    export_btn = gr.Button("📦 حمّل Brand Kit", variant="secondary", visible=False)
    export_file = gr.File(
        label="📄 تحميل Brand Kit PDF",
        visible=False
    )
    gr.Examples(
        examples=[
            [
                "coffee",
                "university students",
                "provide a comfortable place for studying and socializing",
                "modern, friendly, energetic",
                "casual"
            ],
            [
                "streetwear",
                "Gen Z urban creatives",
                "express individuality through bold designs",
                "rebellious, creative, confident",
                "bold"
            ],
        ],
        inputs=[industry, audience, purpose, personality, tone],
    )

    name_btn.click(
        fn=generate_options,
        inputs=[industry, audience, personality, tone, purpose],
        outputs=[
            status,
            packages_state,
            card1,
            card2,
            card3,
            choose1,
            choose2,
            choose3
        ],
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
        outputs=[
            logo_display,
            logo_status,
            logo_btn,
        ],
    )
    export_btn.click(
    fn=export_kit,
    inputs=[chosen_package_state, logo_display],
        outputs=export_file,
    )

if __name__ == "__main__":
    demo.launch(share=True)