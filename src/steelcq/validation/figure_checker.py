"""Automated figure quality and publication standards verification."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from PIL import Image
from ..visualization.style import MIN_PUBLICATION_DPI


class FigureCheckResult:
    """Detailed result of checking a single figure."""

    def __init__(self, filepath: Path, passed: bool, errors: List[str], warnings: List[str], metadata: Optional[dict] = None) -> None:
        self.filepath = filepath
        self.passed = passed
        self.errors = errors
        self.warnings = warnings
        self.metadata = metadata or {}

    def __repr__(self) -> str:
        status = "PASSED" if self.passed else "FAILED"
        return f"<FigureCheckResult {self.filepath.name}: {status} (Errors: {len(self.errors)}, Warnings: {len(self.warnings)})>"


class FigureQualityChecker:
    """Automated checker for Figure PNG compliance (DPI >= 350, integrity, metadata)."""

    def __init__(
        self,
        min_dpi: int = MIN_PUBLICATION_DPI,
        min_width_px: int = 800,
        min_height_px: int = 600,
        require_metadata_json: bool = True
    ) -> None:
        self.min_dpi = min_dpi
        self.min_width_px = min_width_px
        self.min_height_px = min_height_px
        self.require_metadata_json = require_metadata_json

    def check_figure(self, png_path: Union[str, Path]) -> FigureCheckResult:
        """Validate single PNG figure against publication requirements."""
        p = Path(png_path)
        errors: List[str] = []
        warnings: List[str] = []
        meta_dict: Dict = {}

        if not p.exists():
            errors.append(f"Figure file does not exist: {p}")
            return FigureCheckResult(p, False, errors, warnings)

        # Verify PNG header & PIL load
        try:
            with Image.open(p) as img:
                img.verify()
        except Exception as e:
            errors.append(f"PNG file is corrupted or cannot be verified: {e}")
            return FigureCheckResult(p, False, errors, warnings)

        # Inspect image details
        try:
            with Image.open(p) as img:
                width, height = img.size
                info_dpi = img.info.get("dpi")

                if width < self.min_width_px:
                    errors.append(f"Width ({width} px) is below minimum threshold ({self.min_width_px} px).")
                if height < self.min_height_px:
                    errors.append(f"Height ({height} px) is below minimum threshold ({self.min_height_px} px).")

                # Check DPI
                actual_dpi = None
                if info_dpi is not None:
                    # info_dpi can be tuple (xdpi, ydpi)
                    actual_dpi = int(round(info_dpi[0] if isinstance(info_dpi, tuple) else info_dpi))

                if actual_dpi is not None and actual_dpi < self.min_dpi:
                    errors.append(
                        f"Figure DPI ({actual_dpi}) is below required minimum publication DPI ({self.min_dpi})."
                    )
        except Exception as e:
            errors.append(f"Failed to inspect image metrics: {e}")

        # Check metadata JSON file
        json_path = p.with_suffix(".json")
        if self.require_metadata_json:
            if not json_path.exists():
                errors.append(f"Missing mandatory accompanying figure metadata file: {json_path.name}")
            else:
                try:
                    with open(json_path, "r", encoding="utf-8") as jf:
                        meta_dict = json.load(jf)
                    # Check required fields
                    req_fields = ["figure_id", "title", "dpi", "software_versions", "material"]
                    for rf in req_fields:
                        if rf not in meta_dict:
                            errors.append(f"Metadata JSON missing mandatory key: '{rf}'")
                    if meta_dict.get("dpi", 0) < self.min_dpi:
                        errors.append(f"Metadata JSON declares DPI ({meta_dict.get('dpi')}) < {self.min_dpi}")
                except Exception as e:
                    errors.append(f"Error parsing metadata JSON: {e}")

        passed = len(errors) == 0
        return FigureCheckResult(p, passed, errors, warnings, meta_dict)

    def check_directory(self, directory_path: Union[str, Path]) -> Tuple[bool, List[FigureCheckResult]]:
        """Validate all PNGs in a directory tree."""
        dir_p = Path(directory_path)
        pngs = list(dir_p.rglob("*.png"))
        results = [self.check_figure(p) for p in pngs]
        all_passed = all(r.passed for r in results) if results else True
        return all_passed, results
