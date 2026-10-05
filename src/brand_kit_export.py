from PIL import Image, ImageDraw, ImageFont
import re
from matplotlib import font_manager


def export_brand_kit(package: dict, logo_image):
    # High-resolution Brand Kit
    W, H = 1800, 2400

    card = Image.new("RGB", (W, H), "white")
    draw = ImageDraw.Draw(card)

    # Find installed DejaVu Sans fonts safely
    font_regular = font_manager.findfont(
        font_manager.FontProperties(
            family="DejaVu Sans",
            weight="normal"
        )
    )

    font_bold = font_manager.findfont(
        font_manager.FontProperties(
            family="DejaVu Sans",
            weight="bold"
        )
    )

    # High-resolution fonts
    font_title = ImageFont.truetype(font_bold, 96)
    font_body = ImageFont.truetype(font_regular, 48)
    font_small = ImageFont.truetype(font_regular, 36)

    # -------------------------
    # Logo
    # -------------------------
    y = 80

    if logo_image:
        logo_resized = logo_image.resize(
            (600, 600),
            Image.Resampling.LANCZOS
        )

        # Center the logo correctly
        logo_x = (W - 600) // 2

        card.paste(
            logo_resized,
            (logo_x, y)
        )

        y += 680

    # -------------------------
    # Brand Name
    # -------------------------
    name = package.get("brand_name", "—")

    draw.text(
        (W // 2, y),
        name,
        font=font_title,
        fill="black",
        anchor="mm"
    )

    y += 120

    # -------------------------
    # Tagline
    # -------------------------
    tagline = package.get("tagline", "—")

    draw.text(
        (W // 2, y),
        tagline,
        font=font_body,
        fill="#666666",
        anchor="mm"
    )

    y += 120

    # -------------------------
    # Color Palette
    # -------------------------
    colors = package.get("color_palette", [])

    box_size = 120
    gap = 20

    valid_colors = []

    for c in colors:
        match = re.search(
            r'#[0-9A-Fa-f]{6}',
            str(c)
        )

        if match:
            valid_colors.append(
                match.group(0)
            )

    total_width = (
        len(valid_colors) * box_size
        + max(0, len(valid_colors) - 1) * gap
    )

    x_start = (W - total_width) // 2

    for i, hex_code in enumerate(valid_colors):

        x = x_start + i * (box_size + gap)

        draw.rounded_rectangle(
            [
                x,
                y,
                x + box_size,
                y + box_size
            ],
            radius=20,
            fill=hex_code,
            outline="#dddddd",
            width=3
        )

    y += 190

    # -------------------------
    # Typography
    # -------------------------
    draw.text(
        (100, y),
        f"الخط: {package.get('typography', '—')}",
        font=font_small,
        fill="black"
    )

    y += 70

    # -------------------------
    # Visual Style
    # -------------------------
    draw.text(
        (100, y),
        f"الستايل: {package.get('visual_style', '—')}",
        font=font_small,
        fill="black"
    )

    return card