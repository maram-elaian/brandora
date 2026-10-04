import gradio as gr
import subprocess
import sys
import json
import os
import re
import html


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.logo_generator import generate_logo
from src.logo_prompt import build_logo_prompt
from src.brand_kit_export import export_brand_kit

COLOR_RE = re.compile(r"#[0-9A-Fa-f]{6}|#[0-9A-Fa-f]{3}")


def get_brand_packages(brief: dict):
    """
    يشغّل src/run_text_gen.py ويستخرج RESULT_JSON.
    يقبل:
    RESULT_JSON:[{...}, {...}, {...}]
    أو:
    RESULT_JSON:{"packages": [{...}, {...}, {...}]}
    """
    script_path = os.path.join(BASE_DIR, "src", "run_text_gen.py")

    try:
        result = subprocess.run(
            [sys.executable, script_path, json.dumps(brief, ensure_ascii=False)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except Exception as e:
        print("Subprocess error:", e)
        return []

    for line in result.stdout.splitlines():
        if line.startswith("RESULT_JSON:"):
            payload = line[len("RESULT_JSON:"):].strip()
            try:
                data = json.loads(payload)

                if isinstance(data, dict) and "packages" in data:
                    data = data["packages"]

                if isinstance(data, list):
                    return [p for p in data if isinstance(p, dict)]

            except json.JSONDecodeError:
                continue

    if result.stderr:
        print("STDERR:", result.stderr[-1000:])

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


def generate_options(industry, audience, personality, tone, purpose):
    """
    يولّد 3 اقتراحات هوية بصرية.

    outputs:
    status, packages_state, card1, card2, card3, choose1, choose2, choose3
    """
    if not industry or not audience:
        return _empty_ui("⚠️ عبّي الصناعة والجمهور المستهدف على الأقل")

    brief = {
        "industry": industry,
        "target_audience": audience,
        "brand_purpose": purpose,
        "personality": personality,
        "tone": tone,
    }

    packages = get_brand_packages(brief)

    # فلترة أي نتائج فاضية أو غير صالحة
    packages = [
        p for p in packages
        if isinstance(p, dict) and (p.get("brand_name") or p.get("tagline"))
    ]

    if not packages:
        return _empty_ui("❌ فشل التوليد، جربي مرة ثانية")

    if len(packages) >= 3:
        status = ""
    else:
        status = (
            f"⚠️ تم توليد {len(packages)} اقتراحات فقط. "
            "جربي مرة ثانية للحصول على 3 اقتراحات مختلفة."
        )

    cards = []
    buttons = []

    for i in range(3):
        if i < len(packages):
            cards.append(
                gr.update(
                    value=_package_to_html(packages[i]),
                    visible=True
                )
            )
            buttons.append(gr.update(visible=True))
        else:
            cards.append(gr.update(value="", visible=False))
            buttons.append(gr.update(visible=False))

    return (
        status,
        packages,
        cards[0],
        cards[1],
        cards[2],
        buttons[0],
        buttons[1],
        buttons[2],
    )


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
        f"✅ اخترتي: {brand_name}",
        details,
        gr.update(visible=True),
    )


def generate_logo_only(package):
    """
    يولّد اللوجو فقط بعد اختيار باكدج.
    """
    if not package:
        return None

    try:
        logo_prompt = build_logo_prompt(package)
        return generate_logo(logo_prompt)
    except Exception as e:
        print("Logo generation error:", e)
        return None
def export_kit(package, logo_image):
    if package is None:
        return None, gr.update(visible=False)
    kit_image = export_brand_kit(package, logo_image)
    return kit_image, gr.update(visible=True)

with gr.Blocks(
    theme=gr.themes.Soft(primary_hue="violet"),
    title="Brandora"
) as demo:
    gr.Markdown(
        """
        # 🎨 Brandora
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
            label="الشخصية (اختاري أكتر من وحدة)",
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

    gr.Markdown("#### اختاري الاقتراح اللي عجبك")

    with gr.Row():
        with gr.Column():
            card1 = gr.HTML(visible=False)
            choose1 = gr.Button("اختاري هذا ✓", visible=False)

        with gr.Column():
            card2 = gr.HTML(visible=False)
            choose2 = gr.Button("اختاري هذا ✓", visible=False)

        with gr.Column():
            card3 = gr.HTML(visible=False)
            choose3 = gr.Button("اختاري هذا ✓", visible=False)

    gr.Markdown("#### النتيجة النهائية")

    details_display = gr.Markdown()

    logo_btn = gr.Button(
        "🖼️ ولّد اللوجو",
        variant="secondary",
        visible=False
    )

    logo_display = gr.Image(
        label="اللوجو",
        height=300
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

    choose1.click(
        fn=lambda pkgs: choose_package(pkgs, 0),
        inputs=[packages_state],
        outputs=[chosen_package_state, status, details_display, logo_btn],
    )

    choose2.click(
        fn=lambda pkgs: choose_package(pkgs, 1),
        inputs=[packages_state],
        outputs=[chosen_package_state, status, details_display, logo_btn],
    )

    choose3.click(
        fn=lambda pkgs: choose_package(pkgs, 2),
        inputs=[packages_state],
        outputs=[chosen_package_state, status, details_display, logo_btn],
    )

    logo_btn.click(
        fn=generate_logo_only,
        inputs=[chosen_package_state],
        outputs=[logo_display],
    )


if __name__ == "__main__":
    demo.launch(share=True)