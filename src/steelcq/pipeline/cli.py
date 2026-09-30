"""Command-Line Interface (CLI) for the steelcq framework."""

import argparse
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

from ..materials.loader import get_default_aisi4140
from ..validation.qc import QualityControlValidator
from ..thermal_history.history import HeatTreatmentSchedule
from ..visualization.style import apply_publication_style, FIGURE_SIZES, COLOR_PALETTE
from ..visualization.exporter import save_publication_figure
from ..validation.figure_checker import FigureQualityChecker
from .manifest import create_experiment_manifest, save_manifest


def run_demo() -> int:
    """Execute First Coding Task minimal demonstration (Section 84).

    1. Loads AISI 4140.
    2. Validates the composition.
    3. Creates a heat-treatment schedule.
    4. Creates a thermal-history object.
    5. Generates one test PNG.
    6. Verifies that the PNG is >= 350 DPI.
    7. Writes figure metadata.
    8. Verifies QC and FigureChecker.
    """
    print("=" * 72)
    print("  STEELCQ FRAMEWORK: FIRST CODING TASK VERIFICATION (PHASE 1)")
    print("=" * 72)

    # 1. Load AISI 4140
    print("\n[Step 1] Loading AISI 4140 steel material specification...")
    material = get_default_aisi4140()
    print(f"  Loaded Material: {material.name} ({material.standard})")
    print(f"  Composition: {material.composition}")
    print(f"  CE (IIW): {material.carbon_equivalent_iiw():.3f} wt%")

    # 2. Validate composition
    print("\n[Step 2] Executing Pre-simulation Quality Control (QC)...")
    qc_mat = QualityControlValidator.validate_material(material)
    print(f"  QC Passed: {qc_mat.is_valid}")
    print(f"  QC Item Summary: {qc_mat.summary()}")
    if not qc_mat.is_valid:
        print("  ERROR: Material QC validation failed!")
        return 1

    # 3. Create heat-treatment schedule
    print("\n[Step 3] Creating Quenching Heat-Treatment Schedule...")
    schedule = HeatTreatmentSchedule.quenching(
        austenitize_temp_c=845.0,
        heat_time_s=1800.0,
        hold_time_s=2400.0,
        quench_duration_s=120.0
    )
    print(f"  Schedule: {schedule.treatment_name} ({len(schedule.stages)} stages)")

    # 4. Create thermal-history object
    print("\n[Step 4] Synthesizing continuous ThermalHistory trajectory T(t) and dT/dt...")
    thermal_history = schedule.build_thermal_history(num_points_per_stage=200)
    print(f"  Total Duration: {thermal_history.total_duration_s:.1f} s")
    print(f"  Peak Temperature: {thermal_history.max_temperature:.1f} degC")
    print(f"  Min Temperature: {thermal_history.min_temperature:.1f} degC")

    qc_therm = QualityControlValidator.validate_thermal_history(thermal_history)
    print(f"  Thermal History QC Passed: {qc_therm.is_valid}")
    if not qc_therm.is_valid:
        print("  ERROR: Thermal History QC validation failed!")
        return 1

    # 5. Generate test publication figure
    print("\n[Step 5] Generating Publication Figure (T(t) and cooling rate trajectory)...")
    apply_publication_style()

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=FIGURE_SIZES["single_column_tall"], sharex=True)

    t_eval = np.linspace(thermal_history.time[0], thermal_history.time[-1], 1000)
    T_eval = thermal_history.temperature_at(t_eval)
    rate_eval = thermal_history.cooling_rate_at(t_eval)

    # Top: Temperature vs Time
    ax1.plot(t_eval / 60.0, T_eval, color=COLOR_PALETTE["martensite"], lw=1.6, label="Quench T(t)")
    ax1.axhline(845.0, color="#666666", ls=":", lw=1.0, label="Austenitizing (845 C)")
    ax1.axhline(320.0, color="#999999", ls="--", lw=1.0, label="Ms (~320 C)")
    ax1.set_ylabel("Temperature (degC)")
    ax1.set_title("AISI 4140 Quenching Thermal Trajectory")
    ax1.legend(loc="upper right", framealpha=0.85)

    # Bottom: Derivative dT/dt
    ax2.plot(t_eval / 60.0, rate_eval, color=COLOR_PALETTE["classical"], lw=1.4, label="-dT/dt")
    ax2.set_xlabel("Time (minutes)")
    ax2.set_ylabel("Cooling Rate (C/s)")
    ax2.legend(loc="upper right", framealpha=0.85)

    # Output directory
    repo_root = Path(__file__).resolve().parents[3]
    fig_path = repo_root / "figures" / "thermal_history" / "FIG_008_quenching_curve_400dpi.png"

    png_path, json_path = save_publication_figure(
        fig=fig,
        filepath=fig_path,
        figure_id="FIG_008",
        title="Quenching Thermal Trajectory and Cooling Rate for AISI 4140",
        description="Continuous temperature profile T(t) and cooling rate -dT/dt for austenitization and water/oil quench.",
        source_data="analytical_multistage_schedule",
        heat_treatment="Quenching",
        temperature_range=(float(thermal_history.min_temperature), float(thermal_history.max_temperature)),
        units={"time": "minutes", "temperature": "degC", "cooling_rate": "degC/s"},
        dpi=400
    )
    plt.close(fig)
    print(f"  Saved Figure PNG: {png_path.name}")
    print(f"  Saved Metadata:   {json_path.name}")

    # 6. Verify PNG >= 350 DPI and Figure Quality
    print("\n[Step 6] Running Automated Figure Quality Checker...")
    checker = FigureQualityChecker(min_dpi=350)
    check_res = checker.check_figure(png_path)
    print(f"  Figure Check Result: {check_res}")
    if not check_res.passed:
        print(f"  FIGURE VALIDATION FAILED: {check_res.errors}")
        return 1

    # 7. Write Experiment Manifest
    print("\n[Step 7] Generating Reproducible Experiment Manifest...")
    manifest = create_experiment_manifest(
        experiment_id="EXP_DEMO_PHASE1",
        composition=material.composition,
        heat_treatment="Quenching",
        thermal_history_source="synthetic_schedule:Quenching",
        results_summary={
            "duration_s": thermal_history.total_duration_s,
            "max_temp_c": thermal_history.max_temperature,
            "min_temp_c": thermal_history.min_temperature,
            "figure_validation": "PASSED"
        }
    )
    manifest_path = repo_root / "results" / "manifests" / "experiment_demo_manifest.json"
    save_manifest(manifest, manifest_path)
    print(f"  Saved Manifest: {manifest_path.name}")

    print("\n" + "=" * 72)
    print("  FIRST CODING TASK (PHASE 1) VERIFIED SUCCESSFULLY!")
    print("=" * 72)
    return 0


def main() -> None:
    from .runner import EndToEndPipelineRunner

    parser = argparse.ArgumentParser(description="steelcq CLI - Classical & Quantum Steel Heat Treatment Framework")
    parser.add_argument("command", choices=["demo", "run-all"], help="Command to execute")
    args = parser.parse_args()

    if args.command == "demo":
        code = run_demo()
        sys.exit(code)
    elif args.command == "run-all":
        runner = EndToEndPipelineRunner()
        code = runner.run_full_pipeline()
        sys.exit(code)


if __name__ == "__main__":
    main()
