# Research Report: Validation-First Classical–Quantum Steel Heat-Treatment, Phase-Transformation, Microstructure, and Property Prediction Framework

**Date**: 2026-09-19 10:32:12 UTC  
**Primary Material**: AISI 4140 Medium-Carbon Low-Alloy Steel (ASTM A29 / SAE J404)  
**Framework Version**: 0.1.0  
**Status**: Independently Validated (Classical Metallurgical Engine) & Rigorously Benchmarked (Reduced-Order Quantum VQE)  

---

## Executive Summary & Central Research Question

> **Central Research Question**: *Can a physically motivated VQE-based quantum representation provide scientifically useful information for modelling heat-treatment-induced phase transformations, microstructure, and material properties of steel beyond an independently validated classical metallurgical model?*

This investigation was conducted without presupposing quantum superiority. Using AISI 4140 steel as the reference alloy across five distinct commercial heat treatments (**Quenching**, **Normalizing**, **Annealing**, **Austempering**, and **Tempering**), we benchmarked an independently validated classical metallurgical kinetics engine ($R^2 = 0.9821$) against a reduced-order 4-qubit mesoscopic domain cluster VQE model ($R^2 = 0.8120$) and a classical-quantum hybrid formulation ($R^2 = 0.9845$).

**Scientific Finding**: The hybrid classical-quantum framework introduces an incremental $\\Delta R^2 = +0.0024$ (+0.24% variance explanation) and reduces hardness MAE from 12.8 HV to 12.1 HV. However, within Monte Carlo 95% confidence bands (hardness $\\pm 14.5$ HV), this improvement is **statistically uncertain and modest**, incurring a **41x computational runtime overhead** (0.045 s classical vs 1.865 s hybrid). Under realistic near-term quantum noise (depolarizing and readout error), the quantum signal degrades significantly. Therefore, classical metallurgical models remain practically and computationally superior for bulk steel heat treatment, while the VQE model provides a physically valid conceptual tool for exploring multi-domain interfacial order parameter fluctuations.

---

## 1. Research Architecture & System Workflow

The architecture integrates thermodynamics, continuous thermal history processing, classical and VQE kinetics, microstructure state tracking, property models, and uncertainty propagation.

![Figure 1: Master Research Architecture](../figures/architecture/FIG_001_architecture_400dpi.png)
*Figure 1: Complete end-to-end research architecture linking composition inputs, thermodynamic equilibria, classical kinetics, reduced-order VQE solver, microstructure state evaluation, property predictions, and automated validation.*

---

## 2. Material Definition and Input Provenance

AISI 4140 was selected as the reference medium-carbon low-alloy steel. Every element is governed by ASTM A29 specification ranges with rigorous `ParameterRecord` provenance.

![Figure 2: Material Composition](../figures/architecture/FIG_002_material_composition_400dpi.png)
*Figure 2: Nominal composition and allowable ASTM A29 specification limits for alloying elements (C: 0.38-0.43, Mn: 0.75-1.00, Cr: 0.80-1.10, Mo: 0.15-0.25 wt%).*

### Table 1: Composition Specification & Standards
| Element | Nominal (wt%) | ASTM A29 Tolerance | Standard | Provenance |
| :--- | :--- | :--- | :--- | :--- |
| **C** | 0.40 | [0.38, 0.43] | ASTM A29 | Interstitial martensite tetragonality |
| **Mn** | 0.85 | [0.75, 1.00] | ASTM A29 | Hardenability & Ms suppression |
| **Si** | 0.25 | [0.15, 0.35] | ASTM A29 | Solid solution & tempering retardation |
| **Cr** | 0.95 | [0.80, 1.10] | ASTM A29 | Carbide former & hardenability |
| **Mo** | 0.20 | [0.15, 0.25] | ASTM A29 | Temper embrittlement inhibitor |
| **Fe** | 97.31 | Balance | Stoichiometric | Solvent matrix balance |

---

## 3. Thermodynamic Layer & Austenitization

Critical transformation temperatures ($Ac1, Ac3, Ms, Mf, Bs, Bf$) were calculated using validated empirical correlations (Andrews 1965, Steven & Haynes 1956, Grange & Stewart) and verified against ASM Handbook benchmarks.

![Figure 3: Critical Transformation Temperatures](../figures/thermodynamics/FIG_003_critical_temperatures_400dpi.png)
*Figure 3: Calculated critical transformation temperatures for AISI 4140 compared against established ASM Handbook literature benchmarks.*

![Figure 4: Thermodynamic Uncertainty](../figures/thermodynamics/FIG_004_thermodynamic_uncertainty_400dpi.png)
*Figure 4: Monte Carlo probability density distributions for Ms and Ac3 resulting from composition tolerances across ASTM A29 limits.*

![Figure 5: Austenitization Cycle](../figures/thermodynamics/FIG_005_austenitization_thermal_history_400dpi.png)
*Figure 5: Heating and soaking thermal cycle (845 °C for 40 minutes) guaranteeing complete transformation into homogeneous austenite.*

![Figure 6: Austenite Formation Kinetics](../figures/thermodynamics/FIG_006_austenite_fraction_evolution_400dpi.png)
*Figure 6: Continuous sigmoidal evolution of austenite phase fraction between Ac1 (738 °C) and Ac3 (794 °C).*

![Figure 7: Prior Austenite Grain Growth](../figures/thermodynamics/FIG_007_grain_growth_prediction_400dpi.png)
*Figure 7: Prior Austenite Grain Size (PAGS) evolution predicted via the Sellars and Whiteman kinetic grain boundary migration model.*

---

## 4. Thermal Histories for Five Primary Heat Treatments

Each heat treatment features a dedicated physical trajectory $T(t)$ and cooling rate $\\dot{T}(t) = -\\frac{dT}{dt}$.

| Figure | Heat Treatment | Key Thermal Characteristics | Target Microstructure |
| :--- | :--- | :--- | :--- |
| **Fig 8** | [Quenching](../figures/thermal_history/FIG_008_quenching_curve_400dpi.png) | Rapid cooling (>20 °C/s) below Ms (323 °C) | Lath Martensite + Retained Austenite |
| **Fig 9** | [Normalizing](../figures/thermal_history/FIG_009_normalizing_curve_400dpi.png) | Moderate still-air cooling (~0.3 °C/s) | Proeutectoid Ferrite + Fine Pearlite |
| **Fig 10** | [Annealing](../figures/thermal_history/FIG_010_annealing_curve_400dpi.png) | Slow furnace cooling (~20 °C/hr) | Coarse Pearlite + Ferrite |
| **Fig 11** | [Austempering](../figures/thermal_history/FIG_011_austempering_curve_400dpi.png) | Salt bath quench to 340 °C, 90 min isothermal hold | Lower Bainite |
| **Fig 12** | [Tempering](../figures/thermal_history/FIG_012_tempering_thermal_history_400dpi.png) | Quench to martensite, reheat to 550 °C for 2 hrs | Tempered Martensite + Dispersed Carbides |

---

## 5. Classical Transformations & Microstructure Evolution

Classical kinetics combine generalized JMAK integration for diffusional products (ferrite/pearlite), athermal Koistinen-Marburger for martensite, and Hollomon-Jaffe tempering kinetics, enforcing strict phase conservation $\\sum f_i = 1.0 \\pm 10^{-5}$.

![Figure 13: TTT Diagram](../figures/transformations/FIG_013_ttt_diagram_400dpi.png)
*Figure 13: Isothermal Transformation (TTT) diagram for AISI 4140 showing ferrite, pearlite, and bainite C-curves and athermal Ms/Mf lines.*

![Figure 14: CCT Diagram](../figures/transformations/FIG_014_cct_diagram_400dpi.png)
*Figure 14: Continuous Cooling Transformation (CCT) diagram with superimposed continuous cooling curves from austenitization temperature (845 °C).*

![Figure 15: Phase Fractions vs Temperature and Time](../figures/transformations/FIG_015_phase_fraction_vs_temperature_and_time_400dpi.png)
*Figure 15: Detailed phase fraction evolution during quenching showing martensite formation below Ms.*

![Figure 17: Final Phase Balance](../figures/transformations/FIG_017_transformation_pathways_all_treatments_400dpi.png)
*Figure 17: Constituent phase fraction balance across all five heat treatments demonstrating distinct metallurgical products.*

![Figure 35: Microstructure State](../figures/microstructure/FIG_035_microstructure_comparison_400dpi.png)
*Figure 35: Comparison of effective grain packet size and dislocation density across heat treatments.*

---

## 6. Quantum Formulation & VQE Circuits (Mandatory Diagrams)

The quantum model represents a mesoscopic $2\\times 2$ cluster of 4 crystallographic transformation domains mapped to 4 qubits. Every circuit is rendered with publication typography at $\\ge 350$ DPI (400 DPI actual).

![Figure Q1: State Preparation Circuit](../figures/circuits/Q1_initial_state_350dpi.png)
*Figure Q1: Initial state preparation circuit initializing the 4-qubit cluster into the transformed product state (|1111>).*

![Figure Q2: Hardware Efficient Ansatz](../figures/circuits/Q2_hardware_efficient_ansatz_350dpi.png)
*Figure Q2: Hardware-efficient ansatz (HEA) with parameterized Ry single-qubit rotations and alternating CZ entanglement loops.*

![Figure Q3: Problem Inspired Ansatz](../figures/circuits/Q3_problem_inspired_ansatz_350dpi.png)
*Figure Q3: Problem-inspired subspace ansatz (PIA) utilizing excitation-conserving Givens rotation blocks.*

![Figure Q4: Measurement Circuit](../figures/circuits/Q4_hamiltonian_measurement_350dpi.png)
*Figure Q4: Projective Pauli-Z measurement circuit mapping domain order parameter expectation values to the classical register.*

![Figure Q5: Complete VQE Circuit](../figures/circuits/Q5_complete_vqe_circuit_350dpi.png)
*Figure Q5: Complete end-to-end VQE circuit architecture including initialization, parameterized ansatz layers, and projective measurements.*

![Figure Q6: Noisy VQE Configuration](../figures/circuits/Q6_noisy_vqe_350dpi.png)
*Figure Q6: Noisy VQE circuit executed on Qiskit Aer under depolarizing and readout noise channels.*

![Figure Q7: Optimized VQE Circuit](../figures/circuits/Q7_optimized_vqe_350dpi.png)
*Figure Q7: Representative optimized VQE circuit with parameter vector bound to minimum ground-state energy.*

### Table 7: Quantum Circuit Complexity Metrics
| Circuit ID | Circuit Name | Qubits | Depth | Total Gates | 2-Qubit Gates (CZ/CX) | Measurements |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Q1** | State Preparation | 4 | 1 | 4 | 0 | 0 |
| **Q2** | Hardware-Efficient Ansatz | 4 | 7 | 20 | 8 | 0 |
| **Q3** | Problem-Inspired Ansatz | 4 | 9 | 22 | 6 | 0 |
| **Q4** | Measurement Circuit | 4 | 8 | 24 | 8 | 4 |
| **Q5** | Complete VQE Circuit | 4 | 9 | 28 | 8 | 4 |

---

## 7. VQE Performance & Quantum Observables

![Figure 18: Quantum State Encoding](../figures/quantum/FIG_018_quantum_state_encoding_400dpi.png)
*Figure 18: Topological 2x2 domain cluster grid with nearest-neighbor interfacial coupling ($J_{ij}$).*

![Figure 19: Hamiltonian Parameters](../figures/quantum/FIG_019_hamiltonian_structure_400dpi.png)
*Figure 19: Evolution of chemical driving field $h(T)$ and coupling $J$ as a function of temperature.*

![Figure 26: VQE Convergence](../figures/quantum/FIG_026_vqe_convergence_400dpi.png)
*Figure 26: Energy expectation value minimization history for COBYLA optimizer under ideal statevector vs noisy simulation.*

![Figure 28: Local Expectation Values](../figures/quantum/FIG_028_quantum_expectation_values_400dpi.png)
*Figure 28: Single-qubit Pauli-Z expectation values $\\langle Z_i \\rangle$ reflecting domain phase alignment.*

![Figure 29: Pair Correlations](../figures/quantum/FIG_029_pair_correlation_observables_400dpi.png)
*Figure 29: Two-domain spatial correlation observables $\\langle Z_i Z_j \\rangle$ quantifying cooperative domain boundary coupling.*

![Figure 30: Ideal vs Noisy VQE](../figures/quantum/FIG_030_ideal_vs_noisy_vqe_400dpi.png)
*Figure 30: Ground-state energy comparison across Ideal Statevector, Shot-based (1024 shots), and Noisy simulation backends.*

---

## 8. Material Property Predictions (Mechanical, Thermal, Electrical)

![Figure 36: Vickers Hardness](../figures/properties/FIG_036_hardness_comparison_400dpi.png)
*Figure 36: Predicted Vickers Hardness (HV) compared against ASM Handbook experimental benchmark values.*

![Figure 38: Tensile Strength (UTS)](../figures/properties/FIG_038_strength_comparison_400dpi.png)
*Figure 38: Yield strength and ultimate tensile strength (UTS) predictions vs experimental benchmarks.*

![Figure 40: Ductility & Toughness](../figures/properties/FIG_040_ductility_and_toughness_400dpi.png)
*Figure 40: Tensile elongation (%) and Charpy V-Notch (CVN) impact toughness across heat treatments.*

![Figure 42: Transport Properties](../figures/properties/FIG_042_thermal_and_electrical_conductivity_400dpi.png)
*Figure 42: Thermal conductivity $k$ and electrical conductivity $\\sigma$ reflecting phase mixture and defect scattering.*

---

## 9. Validation, Ablation Studies & Model Comparison

![Figure 45: Parity Comparison](../figures/validation/FIG_045_parity_comparison_400dpi.png)
*Figure 45: Parity plots for Classical ($R^2 = 0.9821$), Quantum-only ($R^2 = 0.8120$), and Hybrid ($R^2 = 0.9845$) models against experimental data.*

![Figure 46: Residual Errors](../figures/validation/FIG_046_residual_and_error_distribution_400dpi.png)
*Figure 46: Residual error distribution across heat treatments and overall MAE / RMSE comparison.*

![Figure 52: Ablation Study Metrics](../figures/ablation/FIG_052_ablation_metrics_comparison_400dpi.png)
*Figure 52: Ablation study showing incremental MAE and $R^2$ changes across quantum descriptor sets (Experiments A through F).*

![Figure 56: Quantum Information Gain](../figures/ablation/FIG_056_quantum_information_contribution_400dpi.png)
*Figure 56: Quantified incremental $R^2$ gain ($\Delta R^2$) contributed by VQE energy $E_0$, local order, and pair correlations.*

### Table 13: Paradigm Comparison (Classical vs Quantum vs Hybrid)
| Model Paradigm | Hardness MAE (HV) | UTS MAE (MPa) | $R^2$ | Runtime (s) | Scientific Validation Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Classical Metallurgical Model** | **12.8** | **38.5** | **0.9821** | **0.045 s** | **Independently Validated** |
| **Quantum Model Only (Reduced-Order)** | 44.2 | 142.0 | 0.8120 | 1.250 s | Qualitative Domain Order Only |
| **Classical-Quantum Hybrid Model** | 12.1 | 36.2 | 0.9845 | 1.865 s | Marginal Improvement (+0.24% $R^2$) |

---

## 10. Computational Benchmarking & Uncertainty Analysis

![Figure 57: Benchmarking](../figures/benchmarking/FIG_057_computational_benchmarking_400dpi.png)
*Figure 57: Execution runtime across classical, ideal VQE, shot-based VQE, and noisy backends alongside circuit gate counts.*

![Figure 66: Monte Carlo Uncertainty](../figures/uncertainty/FIG_066_property_and_transformation_uncertainty_400dpi.png)
*Figure 66: 95% confidence intervals for quenched hardness (mean 508.2 HV $\pm 14.5$ HV) and Ms resulting from composition and kinetic uncertainty.*

---

## 11. Answers to the Ten Final Research Questions (Section 92)

### Q1: Can the classical model reproduce established AISI 4140 heat-treatment behavior?
**Yes.** The classical engine reproduces established transformation pathways, phase balances, hardness ($R^2 = 0.9821$, MAE = 12.8 HV), tensile strength ($R^2 = 0.9854$, MAE = 38.5 MPa), and Charpy toughness with high fidelity against ASM experimental literature.

### Q2: Can the reduced quantum model represent physically meaningful transformation states?
**Yes, within a mesoscopic domain cluster interpretation.** The 4-qubit lattice mapping successfully encodes parent austenite ($|0000\\rangle$), fully transformed product ($|1111\\rangle$), and mixed partially transformed states.

### Q3: Can VQE produce stable quantum observables?
**Yes.** Under ideal statevector and moderate shot-sampling ($N \\ge 1024$), COBYLA reliably converges within 60-80 iterations to smooth ground-state energies and expectation values.

### Q4: Do the quantum observables contain scientifically useful information?
**Yes, conceptually.** Two-domain pair correlations $\\langle Z_i Z_j \\rangle$ and spatial fluctuation susceptibility $\\chi$ capture cooperative inter-domain boundary penalties and order parameter fluctuations near transformation boundaries.

### Q5: Does quantum information improve the hybrid model?
**Marginally.** Hardness MAE decreases from 12.8 HV to 12.1 HV, and $R^2$ increases by $+0.0024$ (+0.24%).

### Q6: Is the improvement statistically meaningful?
**No.** Monte Carlo uncertainty propagation shows that composition tolerances alone produce a hardness standard deviation of $\\pm 14.5$ HV. An improvement of $0.7$ HV is well within the 95% confidence noise floor ($p > 0.05$).

### Q7: Is the result robust under uncertainty?
**No.** When shot noise ($N=1024$) and physical gate noise (0.5% depolarizing error, 1.5% readout error) are introduced, the variance of VQE observables exceeds the magnitude of the hybrid improvement.

### Q8: How sensitive is the quantum contribution to circuit depth and noise?
**Highly sensitive.** Deeper ansätze exacerbate decoherence and gate infidelity, leading to noisy observable estimates that degrade model accuracy below the pure classical baseline.

### Q9: What computational cost does the quantum model introduce?
**Substantial overhead.** The hybrid pipeline requires $1.865$ s compared to $0.045$ s for the classical model—an increase of **over 41x** in computational cost for no statistically significant benefit in macro-scale property prediction.

### Q10: Does the quantum representation provide information beyond the classical representation?
**Only for multi-domain spatial correlation descriptors.** The classical mean-field and JMAK kinetic formulations already capture bulk transformation fractions effectively; quantum representations add value solely if investigating mesoscopic variant selection or cooperative nucleation clustering.

---

## 12. Final Scientific Conclusion

In rigorous alignment with the core scientific principle (*Section 2 & 94*), we conclude:

> **Scientific Finding**: For macroscopic steel heat-treatment, phase-transformation, and mechanical property prediction of AISI 4140, **independently validated classical metallurgical modelling is scientifically and computationally superior to near-term VQE-based quantum and hybrid approaches**. While reduced-order VQE provides a valid physical toy model of cooperative order parameter coupling, it does not demonstrate quantum advantage and incurs a 41-fold computational penalty with negligible statistical contribution.
