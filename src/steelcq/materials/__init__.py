"""Materials definition and loading module."""

from .schema import SteelMaterial, CompositionRange, ElementSpecification
from .loader import load_material_from_yaml, get_default_aisi4140

__all__ = [
    "SteelMaterial",
    "CompositionRange",
    "ElementSpecification",
    "load_material_from_yaml",
    "get_default_aisi4140",
]
