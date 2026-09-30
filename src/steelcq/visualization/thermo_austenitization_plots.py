"""Generator for publication figures covering Material, Thermodynamics, Austenitization, and Thermal Histories."""

from pathlib import Path
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
import numpy as np

from ..materials.loader import get_default_aisi4140
from ..thermodynamics.critical_temperatures import ThermodynamicModel
from ..austenitization.kinetics import AustenitizationEngine
from ..thermal_history.history import HeatTreatmentSchedule, ThermalHistory
from ..visualization.style import apply_publication_style, COLOR_PALETTE, FIGURE_SIZES
from ..visualization.exporter import save_publication_figure
from ..validation.figure_checker import FigureQualityChecker


def generate_all_thermo_and_thermal_figures(output_base_dir: Path) -> List[Tuple[Path, Path]]:
    """Generate publication Figures 2 through 12 at 400 DPI with full metadata."""
    apply_publication_style()
    material = get_default_aisi4140()
    thermo = ThermodynamicModel(material)
    crit_temps = thermo.compute_all()
    aust_engine = AustenitizationEngine(material, crit_temps)

    saved_files: List[Tuple[Path, Path]] = []

    # -------------------------------------------------------------------------
    # FIG_002: AISI 4140 Composition Representation
    # -------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=FIGURE_SIZES["single_column"])
    elements = ["C", "Mn", "Si", "Cr", "Mo", "P", "S"]
    nominals = [material.get_element(el) for el in elements]
    lows = [material.composition_ranges[el][0] for el in elements]
    highs = [material.composition_ranges[el][1] for el in elements]
    err_low = [nom - low for nom, low in zip(nominals, lows)]
    err_high = [high - nom for nom, high in zip(nominals, highs)]

    x = np.arange(len(elements))
    bars = ax.bar(x, nominals, yerr=[err_low, err_high], capsize=3, color=COLOR_PALETTE["classical"], alpha=0.85, edgecolor="black", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(elements)
    ax.set_ylabel("Concentration (wt%)")
    ax.set_title("AISI 4140 Nominal Composition & Specification Bounds")
    ax.grid(axis="y", ls="--", alpha=0.6)

    for bar, nom in zip(bars, nominals):
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2.0, yval + 0.12, f"{nom:.2f}", ha="center", va="bottom", fontsize=7.0)

    f2_png, f2_json = save_publication_figure(
        fig=fig,
        filepath=output_base_dir / "architecture" / "FIG_002_material_composition_400dpi.png",
        figure_id="FIG_002",
        title="AISI 4140 Alloying Composition and ASTM A29 Ranges",
        description="Nominal concentrations and tolerance ranges for key alloying elements in AISI 4140 steel.",
        units={"concentration": "wt%"},
        dpi=400
    )
    plt.close(fig)
    saved_files.append((f2_png, f2_json))

    # -------------------------------------------------------------------------
    # FIG_003: Critical Transformation Temperatures & Literature Comparison
    # -------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=FIGURE_SIZES["single_column"])
    labels = ["Ac1", "Ac3", "Bs", "Ms", "Mf"]
    calc_vals = [crit_temps.Ac1, crit_temps.Ac3, crit_temps.Bs, crit_temps.Ms, crit_temps.Mf]
    # ASM Handbook Vol 1 & 4 literature benchmarks for AISI 4140
    lit_vals = [745.0, 800.0, 540.0, 330.0, 120.0]
    lit_unc = [10.0, 12.0, 15.0, 10.0, 20.0]

    y_pos = np.arange(len(labels))
    ax.errorbar(lit_vals, y_pos - 0.15, xerr=lit_unc, fmt="s", color=COLOR_PALETTE["experimental"], label="ASM Literature", capsize=3, markersize=5)
    ax.scatter(calc_vals, y_pos + 0.15, marker="o", color=COLOR_PALETTE["classical"], s=45, label="Model Calculated", zorder=3)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels)
    ax.set_xlabel("Temperature (degC)")
    ax.set_title("Critical Transformation Temperatures (AISI 4140)")
    ax.legend(loc="upper right")
    ax.set_xlim(50, 900)

    f3_png, f3_json = save_publication_figure(
        fig=fig,
        filepath=output_base_dir / "thermodynamics" / "FIG_003_critical_temperatures_400dpi.png",
        figure_id="FIG_003",
        title="Critical Transformation Temperatures Compared to ASM Literature",
        description="Ac1, Ac3, Bs, Ms, and Mf temperatures calculated via thermodynamic models vs ASM Handbook benchmarks.",
        units={"temperature": "degC"},
        dpi=400
    )
    plt.close(fig)
    saved_files.append((f3_png, f3_json))

    # -------------------------------------------------------------------------
    # FIG_004: Thermodynamic Parameter Uncertainty (Monte Carlo sampling over ASTM range)
    # -------------------------------------------------------------------------
    np.random.seed(42)
    n_mc = 2000
    c_mc = np.random.uniform(0.38, 0.43, n_mc)
    mn_mc = np.random.uniform(0.75, 1.00, n_mc)
    cr_mc = np.random.uniform(0.80, 1.10, n_mc)
    mo_mc = np.random.uniform(0.15, 0.25, n_mc)
    si_mc = np.random.uniform(0.15, 0.35, n_mc)

    ms_samples = 539.0 - (423.0 * c_mc) - (30.4 * mn_mc) - (12.1 * cr_mc) - (7.5 * mo_mc)
    ac3_samples = 910.0 - (203.0 * np.sqrt(c_mc)) + (44.7 * si_mc) + (31.5 * mo_mc) - (30.0 * mn_mc) - (11.0 * cr_mc)

    fig, (ax_ms, ax_ac3) = plt.subplots(1, 2, figsize=FIGURE_SIZES["double_column"])
    ax_ms.hist(ms_samples, bins=35, color=COLOR_PALETTE["martensite"], alpha=0.75, edgecolor="black", lw=0.6, density=True)
    ax_ms.axvline(np.mean(ms_samples), color="black", ls="--", lw=1.2, label=f"Mean: {np.mean(ms_samples):.1f} C")
    ax_ms.set_xlabel("Ms Temperature (degC)")
    ax_ms.set_ylabel("Probability Density")
    ax_ms.set_title("Ms Uncertainty under ASTM 4140 Limits")
    ax_ms.legend()

    ax_ac3.hist(ac3_samples, bins=35, color=COLOR_PALETTE["austenite"], alpha=0.75, edgecolor="black", lw=0.6, density=True)
    ax_ac3.axvline(np.mean(ac3_samples), color="black", ls="--", lw=1.2, label=f"Mean: {np.mean(ac3_samples):.1f} C")
    ax_ac3.set_xlabel("Ac3 Temperature (degC)")
    ax_ac3.set_ylabel("Probability Density")
    ax_ac3.set_title("Ac3 Uncertainty under ASTM 4140 Limits")
    ax_ac3.legend()

    f4_png, f4_json = save_publication_figure(
        fig=fig,
        filepath=output_base_dir / "thermodynamics" / "FIG_004_thermodynamic_uncertainty_400dpi.png",
        figure_id="FIG_004",
        title="Monte Carlo Thermodynamic Parameter Uncertainty",
        description="Probability density distributions for Ms and Ac3 resulting from composition tolerances in ASTM A29.",
        units={"temperature": "degC", "density": "1/degC"},
        dpi=400
    )
    plt.close(fig)
    saved_files.append((f4_png, f4_json))

    # -------------------------------------------------------------------------
    # FIG_005: Austenitization Thermal History
    # -------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=FIGURE_SIZES["single_column"])
    t_heat = np.linspace(0, 1800, 100)
    T_heat = 25.0 + (845.0 - 25.0) * (t_heat / 1800.0)
    t_hold = np.linspace(1800, 4200, 100)
    T_hold = np.full_like(t_hold, 845.0)

    t_full = np.concatenate([t_heat, t_hold]) / 60.0
    T_full = np.concatenate([T_heat, T_hold])

    ax.plot(t_full, T_full, color=COLOR_PALETTE["austenite"], lw=1.8, label="Austenitization Schedule")
    ax.axhline(crit_temps.Ac1, color="#666666", ls=":", label=f"Ac1 ({crit_temps.Ac1:.0f} C)")
    ax.axhline(crit_temps.Ac3, color="#333333", ls="--", label=f"Ac3 ({crit_temps.Ac3:.0f} C)")
    ax.set_xlabel("Time (minutes)")
    ax.set_ylabel("Temperature (degC)")
    ax.set_title("Austenitization Thermal History (Heating & Hold)")
    ax.legend(loc="lower right")

    f5_png, f5_json = save_publication_figure(
        fig=fig,
        filepath=output_base_dir / "thermodynamics" / "FIG_005_austenitization_thermal_history_400dpi.png",
        figure_id="FIG_005",
        title="Austenitization Thermal Cycle",
        description="Heating trajectory from 25 C to 845 C with a 40-minute soaking hold.",
        units={"time": "minutes", "temperature": "degC"},
        dpi=400
    )
    plt.close(fig)
    saved_files.append((f5_png, f5_json))

    # -------------------------------------------------------------------------
    # FIG_006: Austenite Fraction vs Temperature and Time
    # -------------------------------------------------------------------------
    fig, (ax_T, ax_t) = plt.subplots(1, 2, figsize=FIGURE_SIZES["double_column"])
    T_span = np.linspace(700, 850, 300)
    f_gamma_T = aust_engine.austenite_fraction_at_temperature(T_span)

    ax_T.plot(T_span, f_gamma_T, color=COLOR_PALETTE["austenite"], lw=1.8)
    ax_T.axvline(crit_temps.Ac1, color="#666666", ls=":", label="Ac1")
    ax_T.axvline(crit_temps.Ac3, color="#333333", ls="--", label="Ac3")
    ax_T.set_xlabel("Temperature (degC)")
    ax_T.set_ylabel("Austenite Phase Fraction $f_\\gamma$")
    ax_T.set_title("Austenite Formation vs Temperature")
    ax_T.legend()

    # Fraction vs time on continuous heating at 0.5 C/s
    t_heat_s = np.linspace(0, 1800, 300)
    T_heat_prog = 25.0 + 0.455 * t_heat_s
    f_gamma_t = aust_engine.austenite_fraction_at_temperature(T_heat_prog)

    ax_t.plot(t_heat_s / 60.0, f_gamma_t, color=COLOR_PALETTE["martensite"], lw=1.8)
    ax_t.set_xlabel("Heating Time (minutes)")
    ax_t.set_ylabel("Austenite Phase Fraction $f_\\gamma$")
    ax_t.set_title("Austenite Formation Kinetics")

    f6_png, f6_json = save_publication_figure(
        fig=fig,
        filepath=output_base_dir / "thermodynamics" / "FIG_006_austenite_fraction_evolution_400dpi.png",
        figure_id="FIG_006",
        title="Austenite Formation Kinetics vs Temperature and Time",
        description="Sigmoidal evolution of austenite phase fraction between Ac1 and Ac3.",
        units={"fraction": "dimensionless", "temperature": "degC", "time": "minutes"},
        dpi=400
    )
    plt.close(fig)
    saved_files.append((f6_png, f6_json))

    # -------------------------------------------------------------------------
    # FIG_007: Prior Austenite Grain Growth Prediction
    # -------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=FIGURE_SIZES["single_column"])
    holding_times_min = np.linspace(1, 120, 100)
    times_s = holding_times_min * 60.0

    for temp_c, col in zip([845.0, 900.0, 1000.0], [COLOR_PALETTE["classical"], COLOR_PALETTE["pearlite"], COLOR_PALETTE["martensite"]]):
        d_pags = [aust_engine.predict_grain_growth(temp_c, t) for t in times_s]
        ax.plot(holding_times_min, d_pags, label=f"{temp_c:.0f} C", color=col, lw=1.6)

    ax.set_xlabel("Holding Time (minutes)")
    ax.set_ylabel("Prior Austenite Grain Size (um)")
    ax.set_title("Prior Austenite Grain Growth (Sellars-Whiteman)")
    ax.legend(title="Holding Temp")

    f7_png, f7_json = save_publication_figure(
        fig=fig,
        filepath=output_base_dir / "thermodynamics" / "FIG_007_grain_growth_prediction_400dpi.png",
        figure_id="FIG_007",
        title="Prior Austenite Grain Growth as Function of Time and Temperature",
        description="Evolution of PAGS calculated via the Sellars and Whiteman kinetic grain boundary migration model.",
        units={"grain_size": "um", "time": "minutes"},
        dpi=400
    )
    plt.close(fig)
    saved_files.append((f7_png, f7_json))

    # -------------------------------------------------------------------------
    # FIG_009 - FIG_012: The 4 other Thermal Histories (Normalizing, Annealing, Austempering, Tempering)
    # -------------------------------------------------------------------------
    schedules = [
        ("FIG_009", "Normalizing", HeatTreatmentSchedule.normalizing(), "FIG_009_normalizing_curve_400dpi.png"),
        ("FIG_010", "Annealing", HeatTreatmentSchedule.annealing(), "FIG_010_annealing_curve_400dpi.png"),
        ("FIG_011", "Austempering", HeatTreatmentSchedule.austempering(), "FIG_011_austempering_curve_400dpi.png"),
        ("FIG_012", "Tempering", HeatTreatmentSchedule.tempering(), "FIG_012_tempering_thermal_history_400dpi.png")
    ]

    for fig_id, name, sched, fname in schedules:
        th = sched.build_thermal_history(num_points_per_stage=150)
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=FIGURE_SIZES["single_column_tall"], sharex=True)

        t_dense = np.linspace(th.time[0], th.time[-1], 800)
        T_dense = th.temperature_at(t_dense)
        rate_dense = th.cooling_rate_at(t_dense)

        time_unit = "minutes" if th.total_duration_s < 10000 else "hours"
        t_plot = (t_dense / 60.0) if time_unit == "minutes" else (t_dense / 3600.0)

        ax1.plot(t_plot, T_dense, color=COLOR_PALETTE["classical"], lw=1.6, label=f"{name} T(t)")
        ax1.set_ylabel("Temperature (degC)")
        ax1.set_title(f"AISI 4140 {name} Thermal Trajectory")
        ax1.legend(loc="upper right")

        ax2.plot(t_plot, rate_dense, color=COLOR_PALETTE["martensite"], lw=1.4, label="-dT/dt")
        ax2.set_xlabel(f"Time ({time_unit})")
        ax2.set_ylabel("Cooling Rate (C/s)")
        ax2.legend(loc="upper right")

        png_p, json_p = save_publication_figure(
            fig=fig,
            filepath=output_base_dir / "thermal_history" / fname,
            figure_id=fig_id,
            title=f"AISI 4140 {name} Thermal History & Rate Trajectory",
            description=f"Continuous temperature history and rate derivative for {name} heat treatment.",
            heat_treatment=name,
            temperature_range=(float(th.min_temperature), float(th.max_temperature)),
            units={"time": time_unit, "temperature": "degC", "cooling_rate": "degC/s"},
            dpi=400
        )
        plt.close(fig)
        saved_files.append((png_p, json_p))

    return saved_files
