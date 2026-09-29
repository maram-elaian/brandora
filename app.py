import gradio as gr
from src.brand_package import build_brand_package
from src.name_generator import get_name
from src.slogan_generator import get_slogan
from src.logo_generator import generate_logo
from src.logo_prompt import build_logo_prompt
def generate_brand(industry, audience, personality, tone, purpose):
    if not industry or not audience:
        return "⚠️ عبّي الصناعة والجمهور المستهدف على الأقل", "", ""

    brief = {
        "industry": industry,
        "target_audience": audience,
        "brand_purpose": purpose,
        "personality": [p.strip() for p in personality.split(",") if p.strip()],
        "tone": tone,
    }
    package = build_brand_package(brief)
    if package is None:
        return "❌ فشل التوليد، جربي مرة ثانية", "", ""

    name = package.get("brand_name", "—")
    tagline = package.get("tagline", "—")
    colors = package.get("color_palette", [])
    traits = package.get("personality_traits", [])
    logo_prompt = build_logo_prompt(package)
    placeholder_image = generate_logo(logo_prompt)

    name_html = f"<h1 style='text-align:center; font-size:2.5em; margin:0;'>{name}</h1>"
    tagline_html = f"<p style='text-align:center; font-size:1.2em; color:#666; font-style:italic;'>{tagline}</p>"

    swatches = "".join(
        f"<div style='display:inline-block; width:60px; height:60px; "
        f"background:{c}; border-radius:8px; margin:4px; border:1px solid #ddd;' "
        f"title='{c}'></div>"
        for c in colors
    )
    colors_html = f"<div style='text-align:center; margin-top:10px;'>{swatches}</div>"

    traits_html = "".join(
        f"<span style='background:#f0f0f0; padding:6px 14px; border-radius:20px; "
        f"margin:4px; display:inline-block; font-size:0.9em;'>{t}</span>"
        for t in traits
    )
    traits_html = f"<div style='text-align:center; margin-top:12px;'>{traits_html}</div>"

    result_html = name_html + tagline_html + colors_html + traits_html
    typography = package.get("typography", "—")
    visual_style = package.get("visual_style", "—")
    details = f"**الخط المقترح:** {typography}\n\n**الستايل البصري:** {visual_style}"

    return result_html, details, None




with gr.Blocks(theme=gr.themes.Soft(primary_hue="violet"), title="Brandora") as demo:
    gr.Markdown(
        """
        # 🎨 Brandora
        ### مولّد الهوية البصرية بالذكاء الاصطناعي
        """
    )

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("#### وصف البراند")
            industry = gr.Textbox(label="الصناعة", placeholder="مثال: coffee shop")
            audience = gr.Textbox(label="الجمهور المستهدف", placeholder="مثال: university students")
            purpose = gr.Textbox(label="هدف البراند", placeholder="مثال: مكان مريح للدراسة والتجمع", lines=2)
            personality = gr.Textbox(label="الشخصية (مفصولة بفاصلة)", placeholder="modern, friendly, energetic")
            tone = gr.Textbox(label="النبرة", placeholder="casual")
            submit_btn = gr.Button("✨ ولّد الهوية", variant="primary", size="lg")

        with gr.Column(scale=1):
            gr.Markdown("#### النتيجة")
            result_display = gr.HTML()
            details_display = gr.Markdown()
            logo_display = gr.Image(label="اللوجو (قريباً)", height=300)

    gr.Examples(
        examples=[
            ["coffee", "university students", "provide a comfortable place for studying and socializing", "modern, friendly, energetic", "casual"],
            ["streetwear", "Gen Z urban creatives", "express individuality through bold designs", "rebellious, creative, confident", "bold"],
        ],
        inputs=[industry, audience, purpose, personality, tone],
    )

    submit_btn.click(
        fn=generate_brand,
        inputs=[industry, audience, personality, tone, purpose],
        outputs=[result_display, details_display, logo_display],
    )

if __name__ == "__main__":
    demo.launch(share=True)
