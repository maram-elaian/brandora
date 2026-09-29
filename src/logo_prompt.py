def build_logo_prompt(package: dict) -> str:
    visual_style = package.get("visual_style", "minimalist")
    return (
        f"{visual_style} icon, professional corporate branding, "
        f"flat vector design, Adobe Illustrator style, geometric, "
        f"minimalist icon, clean background, no text, no cartoon, no mascot"
    )
