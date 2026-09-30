"""Centralized publication visualization style and colorblind-safe palettes."""

import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt

# Colorblind-safe palette (Wong / Tol inspired for physical metallurgy)
COLOR_PALETTE = {
    "austenite": "#E69F00",        # Orange
    "ferrite": "#56B4E9",          # Sky Blue
    "pearlite": "#009E73",         # Bluish Green
    "bainite": "#F0E442",          # Yellow
    "martensite": "#D55E00",       # Vermilion / Deep Red
    "tempered_martensite": "#CC79A7", # Reddish Purple
    "retained_austenite": "#0072B2",  # Blue
    "classical": "#0072B2",        # Blue
    "quantum": "#D55E00",          # Vermilion
    "hybrid": "#009E73",           # Green
    "experimental": "#000000",     # Black
    "uncertainty_band": "#999999", # Medium Grey
    "grid": "#E0E0E0"              # Light Grey
}

FIGURE_SIZES = {
    "single_column": (3.4, 2.8),     # 3.4 inches width
    "single_column_tall": (3.4, 3.8),
    "double_column": (6.9, 3.8),     # 6.9 inches width
    "double_column_square": (6.9, 6.0),
    "circuit": (7.5, 4.0)            # Wide canvas for quantum circuits
}

MIN_PUBLICATION_DPI = 350
DEFAULT_PUBLICATION_DPI = 400


def apply_publication_style() -> None:
    """Configure matplotlib with consistent, publication-quality typography and aesthetics."""
    plt.style.use("default")
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
        "font.size": 8.5,
        "axes.labelsize": 9.5,
        "axes.titlesize": 10.0,
        "xtick.labelsize": 8.0,
        "ytick.labelsize": 8.0,
        "legend.fontsize": 8.0,
        "legend.frameon": True,
        "legend.framealpha": 0.9,
        "legend.edgecolor": "none",
        "figure.titlesize": 11.0,
        "figure.dpi": DEFAULT_PUBLICATION_DPI,
        "savefig.dpi": DEFAULT_PUBLICATION_DPI,
        "savefig.format": "png",
        "savefig.bbox": "tight",
        "lines.linewidth": 1.5,
        "lines.markersize": 5.0,
        "axes.linewidth": 0.8,
        "grid.linewidth": 0.5,
        "grid.color": COLOR_PALETTE["grid"],
        "grid.linestyle": "--",
        "grid.alpha": 0.7,
        "axes.grid": True,
        "axes.axisbelow": True,
        "xtick.direction": "in",
        "ytick.direction": "in",
        "xtick.major.size": 3.0,
        "ytick.major.size": 3.0,
    })
