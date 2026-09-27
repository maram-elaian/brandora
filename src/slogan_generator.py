from src.brand_package import build_brand_package

def get_slogan(brief: dict, package: dict = None) -> str:
    package = package or build_brand_package(brief)
    return package["tagline"] if package else None
