import gradio as gr
import subprocess, sys, json, os, re
from src.logo_generator import generate_logo
from src.logo_prompt import build_logo_prompt


def get_brand_packages(brief: dict):
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "run_text_gen.py")
    result = subprocess.run(
        [sys.executable, script_path, json.dumps(brief)],
        capture_output=True, text=True
    )
    for line in result.stdout.splitlines():
        if line.startswith("RESULT_JSON:"):
            return json.loads(line[len("RESULT_JSON:"):])
    print("STDERR:", result.stderr)
    return []


def _is_valid_hex(color):
    return bool(re.match(r'^#[0-9A-Fa-f]{6}$', str(color).strip()))


def _package_to_html(package: dict) -> str:
    name = package.get("brand_name", "—")
    tagline = package.get("tagline", "—")
    colors = [c if _is_valid_hex(c) else "#CCCCCC" for c in package.get("color_palette", [])]
    swatches = "".join(
        f"<div style='display:inline-block; width:40px; height:40px; "
        f"background:{c}; border-radius:6px; margin:3px; border:1px solid #ddd;'></div>"
        for c in colors
    )
    return (
        f"<div style='text-align:center; padding:16px; border:1px solid #e0e0e0; border-radius:12px;'>"
        f"<h2 style='margin:0;'>{name}</h2>"
        f"<p style='color:#666; font-style:italic; margin:8px 0;'>{tagline}</p>"
        f"<div>{swatches}</div>"
        f"</div>"
    )


def generate_options(industry, audience, personality, tone, purpose):
    if not industry or not audience:
        empty = gr.update(value="", visible=False)
        return "⚠️ عبّي الصناعة والجمهور المستهدف على الأقل", [], empty, empty, empty, \
               gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)

    brief = {
        "industry": industry,
        "target_audience": audience,
        "brand_purpose": purpose,
        "personality": [p.strip() for p in personality.split(",") if p.strip()],
        "tone": tone,
    }
    packages = get_brand_packages(brief)
    if not packages:
        empty = gr.update(value="", visible=False)
        return "❌ فشل التوليد، جربي مرة ثانية", [], empty, empty, empty, \
               gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)

    # نكمّل لـ3 بطاقات حتى لو طلعت أقل (نادر)
    while len(packages) < 3:
        packages.append(packages[-1])

    cards = [gr.update(value=_package_to_html(p), visible=True) for p in packages[:3]]
    buttons = [gr.update(visible=True) for _ in range(3)]

    return "", packages[:3], cards[0], cards[1], cards[2], buttons[0], buttons[1], buttons[2]


def choose_package(packages, index):
    chosen = packages[index]
    details = f"**الخط المقترح:** {chosen.get('typography', '—')}\n\n**الستايل البصري:** {chosen.get('visual_style', '—')}"
    return chosen, f"✅ اخترتي: {chosen.get('brand_name', '—')}", details, gr.update(visible=True)


def generate_logo_only(package):
    if package is None:
        return None
    logo_prompt = build_logo_prompt(package)
    return generate_logo(logo_prompt)


with gr.Blocks(theme=gr.themes.Soft(primary_hue="violet"), title="Brandora") as demo:
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
        industry = gr.Textbox(label="الصناعة", placeholder="مثال: coffee shop")
        audience = gr.Textbox(label="الجمهور المستهدف", placeholder="مثال: university students")
    with gr.Row():
        purpose = gr.Textbox(label="هدف البراند", placeholder="مثال: مكان مريح للدراسة والتجمع")
        personality = gr.Textbox(label="الشخصية (مفصولة بفاصلة)", placeholder="modern, friendly, energetic")
        tone = gr.Textbox(label="النبرة", placeholder="casual")

    name_btn = gr.Button("✨ ولّد 3 اقتراحات", variant="primary", size="lg")
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
    logo_btn = gr.Button("🖼️ ولّد اللوجو", variant="secondary", visible=False)
    logo_display = gr.Image(label="اللوجو", height=300)

    gr.Examples(
        examples=[
            ["coffee", "university students", "provide a comfortable place for studying and socializing", "modern, friendly, energetic", "casual"],
            ["streetwear", "Gen Z urban creatives", "express individuality through bold designs", "rebellious, creative, confident", "bold"],
        ],
        inputs=[industry, audience, purpose, personality, tone],
    )

    name_btn.click(
        fn=generate_options,
        inputs=[industry, audience, personality, tone, purpose],
        outputs=[status, packages_state, card1, card2, card3, choose1, choose2, choose3],
    )

    choose1.click(fn=lambda pkgs: choose_package(pkgs, 0), inputs=[packages_state],
                   outputs=[chosen_package_state, status, details_display, logo_btn])
    choose2.click(fn=lambda pkgs: choose_package(pkgs, 1), inputs=[packages_state],
                   outputs=[chosen_package_state, status, details_display, logo_btn])
    choose3.click(fn=lambda pkgs: choose_package(pkgs, 2), inputs=[packages_state],
                   outputs=[chosen_package_state, status, details_display, logo_btn])

    logo_btn.click(
        fn=generate_logo_only,
        inputs=[chosen_package_state],
        outputs=[logo_display],
    )

if __name__ == "__main__":
    demo.launch(share=True)