"""Material loader from YAML configurations."""

from pathlib import Path
from typing import Union
import yaml
from .schema import SteelMaterial
from ..provenance.record import ParameterRecord


def load_material_from_yaml(filepath: Union[str, Path]) -> SteelMaterial:
    """Load SteelMaterial model from structured YAML specification."""
    p = Path(filepath)
    if not p.exists():
        raise FileNotFoundError(f"Material specification file not found: {p}")

    with open(p, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # Convert raw provenance dictionaries to ParameterRecord instances
    provenance_dict = {}
    if "provenance_records" in data and isinstance(data["provenance_records"], dict):
        for key, rec_data in data["provenance_records"].items():
            provenance_dict[key] = ParameterRecord(**rec_data)
        data["provenance_records"] = provenance_dict

    return SteelMaterial(**data)


def get_default_aisi4140() -> SteelMaterial:
    """Retrieve default configured AISI 4140 steel specification."""
    # Find relative to this file
    current_dir = Path(__file__).resolve().parent
    config_path = current_dir.parents[2] / "configs" / "materials" / "AISI4140.yaml"
    return load_material_from_yaml(config_path)
