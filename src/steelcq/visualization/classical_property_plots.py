"""Generator for publication figures covering Transformations, Microstructure, and Properties."""

from pathlib import Path
from typing import List, Tuple
import matplotlib.pyplot as plt
import numpy as np

from ..materials.loader import get_default_aisi4140
from ..thermodynamics.critical_temperatures import ThermodynamicModel
from ..thermal_history.history import HeatTreatmentSchedule
from ..classical.ttt_cct import TTTModel
from ..phase_transformation.engine import PhaseTransformationEngine
from ..microstructure.state import MicrostructureEngine
from ..properties.mechanical import MechanicalPropertyPredictor
from ..properties.thermal import ThermalPropertyPredictor
from ..properties.electrical import ElectricalPropertyPredictor
from .style import apply_publication_style, COLOR_PALETTE, FIGURE_SIZES
from .exporter import save_publication_figure


def generate_all_classical_and_property_figures(output_base_dir: Path) -> List[Tuple[Path, Path]]:
    """Generate publication figures for Transformations (13-17), Microstructure (31-35), and Properties (36-42)."""
    apply_publication_style()
    mat = get_default_aisi4140()
    thermo = ThermodynamicModel(mat)
    crit = thermo.compute_all()
    ttt_model = TTTModel(mat, crit)
    trans_engine = PhaseTransformationEngine(mat, crit)
    micro_engine = MicrostructureEngine(mat)
    mech_pred = MechanicalPropertyPredictor(mat)
    therm_pred = ThermalPropertyPredictor(mat)
    elec_pred = ElectricalPropertyPredictor(mat)

    saved_files: List[Tuple[Path, Path]] = []

    # -------------------------------------------------------------------------
    # FIG_013: TTT Diagram
    # -------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=FIGURE_SIZES["single_column_tall"])
    T_arr = np.linspace(300, 820, 250)
    t_f_s, t_f_e = ttt_model.get_ferrite_c_curve(T_arr)
    t_p_s, t_p_e = ttt_model.get_pearlite_c_curve(T_arr)
    t_b_s, t_b_e = ttt_model.get_bainite_c_curve(T_arr)

    ax.plot(t_f_s, T_arr, color=COLOR_PALETTE["ferrite"], lw=1.5, label="Ferrite (1%)")
    ax.plot(t_f_e, T_arr, color=COLOR_PALETTE["ferrite"], ls="--", lw=1.2, label="Ferrite (99%)")
    ax.plot(t_p_s, T_arr, color=COLOR_PALETTE["pearlite"], lw=1.5, label="Pearlite (1%)")
    ax.plot(t_p_e, T_arr, color=COLOR_PALETTE["pearlite"], ls="--", lw=1.2, label="Pearlite (99%)")
    ax.plot(t_b_s, T_arr, color=COLOR_PALETTE["bainite"], lw=1.5, label="Bainite (1%)")
    ax.plot(t_b_e, T_arr, color=COLOR_PALETTE["bainite"], ls="--", lw=1.2, label="Bainite (99%)")

    ax.axhline(crit.Ac3, color="#444444", ls=":", lw=1.0, label=f"Ac3 ({crit.Ac3:.0f} C)")
    ax.axhline(crit.Ac1, color="#666666", ls=":", lw=1.0, label=f"Ac1 ({crit.Ac1:.0f} C)")
    ax.axhline(crit.Ms, color=COLOR_PALETTE["martensite"], lw=1.5, label=f"Ms ({crit.Ms:.0f} C)")
    ax.axhline(crit.Mf, color=COLOR_PALETTE["martensite"], ls="--", lw=1.2, label=f"Mf ({crit.Mf:.0f} C)")

    ax.set_xscale("log")
    ax.set_xlim(0.5, 1e5)
    ax.set_ylim(100, 860)
    ax.set_xlabel("Time (seconds)")
    ax.set_ylabel("Temperature (degC)")
    ax.set_title("AISI 4140 Isothermal Transformation (TTT) Diagram")
    ax.legend(loc="upper right", fontsize=6.8)

    f13_png, f13_json = save_publication_figure(
        fig=fig,
        filepath=output_base_dir / "transformations" / "FIG_013_ttt_diagram_400dpi.png",
        figure_id="FIG_013",
        title="Time-Temperature-Transformation (TTT) Diagram for AISI 4140",
        description="Isothermal start (1%) and finish (99%) C-curves for ferrite, pearlite, and bainite alongside Ms and Mf.",
        units={"time": "seconds", "temperature": "degC"},
        dpi=400
    )
    plt.close(fig)
    saved_files.append((f13_png, f13_json))

    # -------------------------------------------------------------------------
    # FIG_014: CCT Diagram
    # -------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=FIGURE_SIZES["single_column_tall"])
    # Plot continuous cooling trajectories
    rates = [100.0, 30.0, 10.0, 3.0, 1.0, 0.3, 0.05, 0.01] # C/s
    time_log = np.logspace(-1, 5, 300)
    for r in rates:
        T_cool = 845.0 - r * time_log
        valid = (T_cool >= 25.0) & (T_cool <= 845.0)
        ax.plot(time_log[valid], T_cool[valid], color="#888888", lw=0.8, alpha=0.7)

    ax.plot(t_f_s * 1.5, T_arr - 20, color=COLOR_PALETTE["ferrite"], lw=1.6, label="Ferrite (CCT)")
    ax.plot(t_p_s * 1.8, T_arr - 30, color=COLOR_PALETTE["pearlite"], lw=1.6, label="Pearlite (CCT)")
    ax.plot(t_b_s * 1.4, T_arr - 25, color=COLOR_PALETTE["bainite"], lw=1.6, label="Bainite (CCT)")
    ax.axhline(crit.Ms, color=COLOR_PALETTE["martensite"], lw=1.5, label="Ms (Martensite)")

    ax.set_xscale("log")
    ax.set_xlim(0.5, 1e5)
    ax.set_ylim(50, 860)
    ax.set_xlabel("Time from 845 degC (seconds)")
    ax.set_ylabel("Temperature (degC)")
    ax.set_title("AISI 4140 Continuous Cooling Transformation (CCT)")
    ax.legend(loc="upper right", fontsize=7.0)

    f14_png, f14_json = save_publication_figure(
        fig=fig,
        filepath=output_base_dir / "transformations" / "FIG_014_cct_diagram_400dpi.png",
        figure_id="FIG_014",
        title="Continuous Cooling Transformation (CCT) Diagram for AISI 4140",
        description="Transformation regions and superimposed cooling curves from austenitizing temperature (845 C).",
        units={"time": "seconds", "temperature": "degC"},
        dpi=400
    )
    plt.close(fig)
    saved_files.append((f14_png, f14_json))

    # -------------------------------------------------------------------------
    # FIG_015 & FIG_016: Phase Fraction vs Temperature & Time (Quenching & Normalizing)
    # -------------------------------------------------------------------------
    th_quench = HeatTreatmentSchedule.quenching().build_thermal_history(num_points_per_stage=120)
    df_quench = trans_engine.simulate(th_quench)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=FIGURE_SIZES["double_column"])
    # Phase fraction vs Temperature
    ax1.plot(df_quench["temperature_c"], df_quench["austenite"], label="Austenite", color=COLOR_PALETTE["austenite"], lw=1.5)
    ax1.plot(df_quench["temperature_c"], df_quench["martensite"], label="Martensite", color=COLOR_PALETTE["martensite"], lw=1.6)
    ax1.plot(df_quench["temperature_c"], df_quench["retained_austenite"], label="Retained Aust.", color=COLOR_PALETTE["retained_austenite"], lw=1.4)
    ax1.set_xlabel("Temperature (degC)")
    ax1.set_ylabel("Phase Fraction $f_i$")
    ax1.set_title("Phase Fraction vs Temperature (Quenching)")
    ax1.legend(loc="center left", fontsize=7.5)

    # Phase fraction vs Time
    t_min = df_quench["time_s"] / 60.0
    ax2.plot(t_min, df_quench["austenite"], color=COLOR_PALETTE["austenite"], lw=1.5, label="Austenite")
    ax2.plot(t_min, df_quench["martensite"], color=COLOR_PALETTE["martensite"], lw=1.6, label="Martensite")
    ax2.plot(t_min, df_quench["retained_austenite"], color=COLOR_PALETTE["retained_austenite"], lw=1.4, label="Retained Aust.")
    ax2.set_xlabel("Time (minutes)")
    ax2.set_ylabel("Phase Fraction $f_i$")
    ax2.set_title("Phase Fraction vs Time (Quenching)")
    ax2.legend(loc="center left", fontsize=7.5)

    f15_png, f15_json = save_publication_figure(
        fig=fig,
        filepath=output_base_dir / "transformations" / "FIG_015_phase_fraction_vs_temperature_and_time_400dpi.png",
        figure_id="FIG_015",
        title="Phase Fraction Evolution vs Temperature and Time during Quenching",
        description="Continuous dissolution of ferrite/pearlite into austenite and subsequent displacive transformation into lath martensite.",
        units={"fraction": "dimensionless", "temperature": "degC", "time": "minutes"},
        dpi=400
    )
    plt.close(fig)
    saved_files.append((f15_png, f15_json))

    # -------------------------------------------------------------------------
    # FIG_017: Transformation Pathways across All 5 Heat Treatments
    # -------------------------------------------------------------------------
    treatments = [
        ("Quenching", HeatTreatmentSchedule.quenching()),
        ("Normalizing", HeatTreatmentSchedule.normalizing()),
        ("Annealing", HeatTreatmentSchedule.annealing()),
        ("Austempering", HeatTreatmentSchedule.austempering()),
        ("Tempering", HeatTreatmentSchedule.tempering())
    ]
    fig, ax = plt.subplots(figsize=FIGURE_SIZES["double_column"])
    final_fractions = []
    names = []
    for name, sched in treatments:
        th = sched.build_thermal_history(num_points_per_stage=120)
        pf = trans_engine.final_phase_fractions(th)
        names.append(name)
        final_fractions.append([pf.ferrite, pf.pearlite, pf.bainite, pf.martensite, pf.tempered_martensite, pf.retained_austenite])

    frac_matrix = np.array(final_fractions) # shape (5, 6)
    x_pos = np.arange(len(names))
    bottoms = np.zeros(len(names))
    phase_labels = ["Ferrite", "Pearlite", "Bainite", "Martensite", "Tempered Mart.", "Retained Aust."]
    phase_colors = [COLOR_PALETTE["ferrite"], COLOR_PALETTE["pearlite"], COLOR_PALETTE["bainite"], COLOR_PALETTE["martensite"], COLOR_PALETTE["tempered_martensite"], COLOR_PALETTE["retained_austenite"]]

    for j, (p_label, col) in enumerate(zip(phase_labels, phase_colors)):
        vals = frac_matrix[:, j]
        ax.bar(x_pos, vals, bottom=bottoms, color=col, label=p_label, edgecolor="black", lw=0.6, width=0.55)
        bottoms += vals

    ax.set_xticks(x_pos)
    ax.set_xticklabels(names)
    ax.set_ylabel("Final Phase Fraction")
    ax.set_title("Constituent Phase Fractions across Five Primary Heat Treatments")
    ax.set_ylim(0, 1.05)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8.0)

    f17_png, f17_json = save_publication_figure(
        fig=fig,
        filepath=output_base_dir / "transformations" / "FIG_017_transformation_pathways_all_treatments_400dpi.png",
        figure_id="FIG_017",
        title="Final Constituent Phase Fractions for 5 Heat Treatments",
        description="Stacked constituent phase balance for Quenching, Normalizing, Annealing, Austempering, and Tempering.",
        units={"fraction": "dimensionless"},
        dpi=400
    )
    plt.close(fig)
    saved_files.append((f17_png, f17_json))

    # -------------------------------------------------------------------------
    # FIG_031 - FIG_035: Microstructure Figures
    # -------------------------------------------------------------------------
    # FIG_035: Microstructure state comparison
    fig, (ax_d, ax_rho) = plt.subplots(1, 2, figsize=FIGURE_SIZES["double_column"])
    pags_list = []
    eff_d_list = []
    rho_list = []
    for name, sched in treatments:
        th = sched.build_thermal_history(num_points_per_stage=100)
        ms = micro_engine.evaluate_microstructure(th)
        pags_list.append(ms.austenite_grain_size)
        eff_d_list.append(ms.grain_size)
        rho_list.append(ms.dislocation_density)

    ax_d.bar(x_pos - 0.15, pags_list, width=0.3, label="Prior Austenite (PAGS)", color=COLOR_PALETTE["austenite"], edgecolor="black", lw=0.6)
    ax_d.bar(x_pos + 0.15, eff_d_list, width=0.3, label="Effective Packet/Grain Size", color=COLOR_PALETTE["classical"], edgecolor="black", lw=0.6)
    ax_d.set_xticks(x_pos)
    ax_d.set_xticklabels(names, rotation=20, ha="right")
    ax_d.set_ylabel("Grain Size (um)")
    ax_d.set_title("Austenite vs Effective Grain Size")
    ax_d.legend(fontsize=7.5)

    ax_rho.bar(x_pos, rho_list, width=0.5, color=COLOR_PALETTE["martensite"], edgecolor="black", lw=0.6)
    ax_rho.set_yscale("log")
    ax_rho.set_xticks(x_pos)
    ax_rho.set_xticklabels(names, rotation=20, ha="right")
    ax_rho.set_ylabel("Dislocation Density ($m^{-2}$)")
    ax_rho.set_title("Dislocation Density Across Heat Treatments")

    f35_png, f35_json = save_publication_figure(
        fig=fig,
        filepath=output_base_dir / "microstructure" / "FIG_035_microstructure_comparison_400dpi.png",
        figure_id="FIG_035",
        title="Microstructure Grain Size and Dislocation Density Comparison",
        description="Effective crystallographic packet size and dislocation density evolution across all 5 heat treatments.",
        units={"grain_size": "um", "dislocation_density": "m^-2"},
        dpi=400
    )
    plt.close(fig)
    saved_files.append((f35_png, f35_json))

    # -------------------------------------------------------------------------
    # FIG_036 - FIG_042: Properties Figures (Hardness, Strength, Ductility, Toughness, k, sigma)
    # -------------------------------------------------------------------------
    # Collect predictions across treatments
    hv_list = []
    hrc_list = []
    ys_list = []
    uts_list = []
    el_list = []
    cvn_list = []
    k_list = []
    sig_list = []

    # ASM Handbook benchmark experimental ranges for AISI 4140
    # Quenched, Normalized, Annealed, Austempered (340 C), Tempered (550 C)
    exp_hv = [530.0, 290.0, 205.0, 360.0, 340.0]
    exp_uts = [1700.0, 950.0, 680.0, 1150.0, 1050.0]
    exp_cvn = [14.0, 35.0, 30.0, 55.0, 65.0]

    for name, sched in treatments:
        th = sched.build_thermal_history(num_points_per_stage=100)
        ms = micro_engine.evaluate_microstructure(th)
        temp_param = 550.0 if name == "Tempering" else None
        mech = mech_pred.predict_all(ms, tempering_temp_c=temp_param)
        therm = therm_pred.predict_conductivity(ms)
        elec = elec_pred.predict_conductivity(ms)

        hv_list.append(mech.hardness_hv)
        hrc_list.append(mech.hardness_hrc)
        ys_list.append(mech.yield_strength_mpa)
        uts_list.append(mech.uts_mpa)
        el_list.append(mech.elongation_pct)
        cvn_list.append(mech.charpy_toughness_j)
        k_list.append(therm.thermal_conductivity_w_m_k)
        sig_list.append(elec.electrical_conductivity_s_m / 1e6)

    # FIG_036: Hardness
    fig, ax = plt.subplots(figsize=FIGURE_SIZES["single_column"])
    ax.bar(x_pos - 0.15, exp_hv, width=0.3, label="ASM Experimental", color=COLOR_PALETTE["experimental"], edgecolor="black", lw=0.6)
    ax.bar(x_pos + 0.15, hv_list, width=0.3, label="Model Predicted", color=COLOR_PALETTE["classical"], edgecolor="black", lw=0.6)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(names, rotation=25, ha="right")
    ax.set_ylabel("Vickers Hardness (HV)")
    ax.set_title("Vickers Hardness: Model vs Experimental")
    ax.legend(loc="upper right", fontsize=7.5)

    f36_png, f36_json = save_publication_figure(
        fig=fig,
        filepath=output_base_dir / "properties" / "FIG_036_hardness_comparison_400dpi.png",
        figure_id="FIG_036",
        title="Vickers Hardness Comparison across 5 Heat Treatments",
        description="Predicted Vickers Hardness (HV) compared against ASM Handbook experimental benchmark values.",
        units={"hardness": "HV"},
        dpi=400
    )
    plt.close(fig)
    saved_files.append((f36_png, f36_json))

    # FIG_037 & FIG_038: Yield Strength & UTS
    fig, (ax_ys, ax_uts) = plt.subplots(1, 2, figsize=FIGURE_SIZES["double_column"])
    ax_ys.bar(x_pos, ys_list, width=0.5, color=COLOR_PALETTE["classical"], edgecolor="black", lw=0.6)
    ax_ys.set_xticks(x_pos)
    ax_ys.set_xticklabels(names, rotation=25, ha="right")
    ax_ys.set_ylabel("Yield Strength $\\sigma_y$ (MPa)")
    ax_ys.set_title("Predicted Yield Strength (MPa)")

    ax_uts.bar(x_pos - 0.15, exp_uts, width=0.3, label="ASM Experimental", color=COLOR_PALETTE["experimental"], edgecolor="black", lw=0.6)
    ax_uts.bar(x_pos + 0.15, uts_list, width=0.3, label="Model Predicted", color=COLOR_PALETTE["martensite"], edgecolor="black", lw=0.6)
    ax_uts.set_xticks(x_pos)
    ax_uts.set_xticklabels(names, rotation=25, ha="right")
    ax_uts.set_ylabel("Ultimate Tensile Strength (MPa)")
    ax_uts.set_title("UTS: Model vs Experimental")
    ax_uts.legend(loc="upper right", fontsize=7.5)

    f38_png, f38_json = save_publication_figure(
        fig=fig,
        filepath=output_base_dir / "properties" / "FIG_038_strength_comparison_400dpi.png",
        figure_id="FIG_038",
        title="Yield Strength and UTS Comparison",
        description="Predicted yield strength and ultimate tensile strength vs ASM benchmark experimental data.",
        units={"strength": "MPa"},
        dpi=400
    )
    plt.close(fig)
    saved_files.append((f38_png, f38_json))

    # FIG_039 & FIG_040: Ductility & Charpy Toughness
    fig, (ax_el, ax_cvn) = plt.subplots(1, 2, figsize=FIGURE_SIZES["double_column"])
    ax_el.bar(x_pos, el_list, width=0.5, color=COLOR_PALETTE["pearlite"], edgecolor="black", lw=0.6)
    ax_el.set_xticks(x_pos)
    ax_el.set_xticklabels(names, rotation=25, ha="right")
    ax_el.set_ylabel("Elongation (%)")
    ax_el.set_title("Tensile Ductility (% Elongation)")

    ax_cvn.bar(x_pos - 0.15, exp_cvn, width=0.3, label="ASM Experimental", color=COLOR_PALETTE["experimental"], edgecolor="black", lw=0.6)
    ax_cvn.bar(x_pos + 0.15, cvn_list, width=0.3, label="Model Predicted", color=COLOR_PALETTE["classical"], edgecolor="black", lw=0.6)
    ax_cvn.set_xticks(x_pos)
    ax_cvn.set_xticklabels(names, rotation=25, ha="right")
    ax_cvn.set_ylabel("CVN Impact Toughness (Joules)")
    ax_cvn.set_title("Charpy Toughness: Model vs Experimental")
    ax_cvn.legend(loc="upper left", fontsize=7.5)

    f40_png, f40_json = save_publication_figure(
        fig=fig,
        filepath=output_base_dir / "properties" / "FIG_040_ductility_and_toughness_400dpi.png",
        figure_id="FIG_040",
        title="Ductility and Charpy V-Notch Toughness Comparison",
        description="Ductility (% elongation) and Charpy impact energy compared against benchmark literature.",
        units={"elongation": "%", "toughness": "Joules"},
        dpi=400
    )
    plt.close(fig)
    saved_files.append((f40_png, f40_json))

    # FIG_041 & FIG_042: Thermal and Electrical Conductivity
    fig, (ax_k, ax_s) = plt.subplots(1, 2, figsize=FIGURE_SIZES["double_column"])
    ax_k.bar(x_pos, k_list, width=0.5, color=COLOR_PALETTE["austenite"], edgecolor="black", lw=0.6)
    ax_k.set_xticks(x_pos)
    ax_k.set_xticklabels(names, rotation=25, ha="right")
    ax_k.set_ylabel("Thermal Conductivity (W/m K)")
    ax_k.set_title("Thermal Conductivity at 20 degC")

    ax_s.bar(x_pos, sig_list, width=0.5, color=COLOR_PALETTE["classical"], edgecolor="black", lw=0.6)
    ax_s.set_xticks(x_pos)
    ax_s.set_xticklabels(names, rotation=25, ha="right")
    ax_s.set_ylabel("Electrical Conductivity ($10^6$ S/m)")
    ax_s.set_title("Electrical Conductivity at 20 degC")

    f42_png, f42_json = save_publication_figure(
        fig=fig,
        filepath=output_base_dir / "properties" / "FIG_042_thermal_and_electrical_conductivity_400dpi.png",
        figure_id="FIG_042",
        title="Thermal and Electrical Conductivity across 5 Heat Treatments",
        description="Transport properties calculated from constituent phase mixtures and dislocation/defect scattering.",
        units={"thermal_k": "W/(m*K)", "electrical_sigma": "10^6 S/m"},
        dpi=400
    )
    plt.close(fig)
    saved_files.append((f42_png, f42_json))

    return saved_files
