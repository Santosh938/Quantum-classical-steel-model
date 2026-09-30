"""Figure exporter and metadata generator ensuring >=350 DPI publication compliance."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union
import matplotlib.pyplot as plt
from pydantic import BaseModel, Field
from PIL import Image

from .style import MIN_PUBLICATION_DPI, DEFAULT_PUBLICATION_DPI


class FigureMetadata(BaseModel):
    """Metadata schema accompanying every publication figure."""
    figure_id: str
    title: str
    description: str
    source_data: str
    model_version: str = "0.1.0"
    parameter_version: str = "2026.1"
    material: str = "AISI 4140"
    heat_treatment: Optional[str] = None
    temperature_range: Optional[Tuple[float, float]] = None
    units: Dict[str, str] = Field(default_factory=dict)
    dpi: int = DEFAULT_PUBLICATION_DPI
    width_in: float
    height_in: float
    width_px: int
    height_px: int
    software_versions: Dict[str, str] = Field(default_factory=dict)
    random_seed: int = 42
    date: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    git_commit: str = "HEAD"


def get_software_versions() -> Dict[str, str]:
    """Retrieve runtime versions of core scientific libraries."""
    import numpy as np
    import scipy as sp
    import matplotlib as mpl
    import pydantic
    versions = {
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "scipy": sp.__version__,
        "matplotlib": mpl.__version__,
        "pydantic": pydantic.__version__
    }
    try:
        import qiskit
        versions["qiskit"] = qiskit.__version__
    except ImportError:
        pass
    return versions


def save_publication_figure(
    fig: plt.Figure,
    filepath: Union[str, Path],
    figure_id: str,
    title: str,
    description: str,
    source_data: str = "computed",
    heat_treatment: Optional[str] = None,
    temperature_range: Optional[Tuple[float, float]] = None,
    units: Optional[Dict[str, str]] = None,
    dpi: int = DEFAULT_PUBLICATION_DPI,
    random_seed: int = 42
) -> Tuple[Path, Path]:
    """Save matplotlib Figure as PNG at >=350 DPI and write accompanying JSON metadata.

    Returns:
        (png_path, json_path)
    """
    if dpi < MIN_PUBLICATION_DPI:
        raise ValueError(
            f"DPI {dpi} violates Section 47 mandate (minimum required is {MIN_PUBLICATION_DPI} DPI)."
        )

    out_png = Path(filepath)
    if out_png.suffix.lower() != ".png":
        out_png = out_png.with_suffix(".png")

    out_png.parent.mkdir(parents=True, exist_ok=True)
    out_json = out_png.with_suffix(".json")

    # Save figure
    fig.savefig(out_png, dpi=dpi, format="png", bbox_inches="tight")

    # Inspect rendered dimensions via PIL
    with Image.open(out_png) as img:
        width_px, height_px = img.size

    w_in, h_in = fig.get_size_inches()

    meta = FigureMetadata(
        figure_id=figure_id,
        title=title,
        description=description,
        source_data=source_data,
        material="AISI 4140",
        heat_treatment=heat_treatment,
        temperature_range=temperature_range,
        units=units or {},
        dpi=dpi,
        width_in=round(float(w_in), 3),
        height_in=round(float(h_in), 3),
        width_px=width_px,
        height_px=height_px,
        software_versions=get_software_versions(),
        random_seed=random_seed
    )

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(meta.model_dump(), f, indent=2)

    return out_png, out_json
