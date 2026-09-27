import gradio as gr
from src.brand_package import build_brand_package
from src.name_generator import get_name
from src.slogan_generator import get_slogan

def generate_brand(industry, audience, personality, tone, purpose):
    brief = {
        "industry": industry,
        "target_audience": audience,
        "brand_purpose": purpose,
        "personality": [p.strip() for p in personality.split(",")],
        "tone": tone,
    }
    package = build_brand_package(brief)
    if package is None:
        return "فشل التوليد، جربي مرة ثانية", "", None

    name = get_name(brief, package)
    tagline = get_slogan(brief, package)
    colors = ", ".join(package.get("color_palette", []))

    # placeholder للوجو لحد ما يتحدد الموديل النهائي
    placeholder_image = None

    return f"{name}", f"{tagline}\nالألوان: {colors}", placeholder_image

demo = gr.Interface(
    fn=generate_brand,
    inputs=[
        gr.Textbox(label="الصناعة"),
        gr.Textbox(label="الجمهور المستهدف"),
        gr.Textbox(label="الشخصية (مفصولة بفاصلة)"),
        gr.Textbox(label="النبرة"),
        gr.Textbox(label="هدف البراند"),
    ],
    outputs=[
        gr.Textbox(label="اسم البراند"),
        gr.Textbox(label="الشعار والألوان"),
        gr.Image(label="اللوجو (قريباً)"),
    ],
    title="Brandora"
)

if __name__ == "__main__":
    demo.launch(share=True)
