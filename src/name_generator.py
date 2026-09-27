from src.brand_package import build_brand_package

def get_name(brief: dict, package: dict = None) -> str:
    package = package or build_brand_package(brief)
    return package["brand_name"] if package else None
