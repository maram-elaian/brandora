def build_logo_prompt(package: dict) -> str:
    visual_style = package.get("visual_style", "minimalist")
    colors = package.get("color_palette", [])

    color_phrase = ""
    if colors:
        color_phrase = f"color palette: {', '.join(colors)}, "

    return (
        f"{visual_style} icon, {color_phrase}"
        f"professional corporate branding, "
        f"flat vector design, Adobe Illustrator style, geometric, "
        f"minimalist icon, clean background, no text, no cartoon, no mascot"
    )