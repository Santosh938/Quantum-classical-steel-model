"""Monte Carlo uncertainty propagation from composition, thermodynamics, and noise to microstructure and properties."""

from typing import Dict, List, Optional
import numpy as np
from pydantic import BaseModel, Field

from ..materials.schema import SteelMaterial
from ..thermodynamics.critical_temperatures import ThermodynamicModel
from ..thermal_history.history import ThermalHistory
from ..phase_transformation.engine import PhaseTransformationEngine
from ..microstructure.state import MicrostructureEngine
from ..properties.mechanical import MechanicalPropertyPredictor


class UncertaintySummary(BaseModel):
    """Statistical distribution metrics for a predicted material property."""
    mean: float
    std: float
    ci_95: tuple[float, float]
    p10: float
    p50: float
    p90: float
    samples_count: int


class MonteCarloUncertaintyPropagator:
    """Propagates input uncertainty distributions through entire metallurgical workflow."""

    def __init__(self, base_material: SteelMaterial, num_samples: int = 250, seed: int = 42) -> None:
        self.base_material = base_material
        self.num_samples = num_samples
        self.seed = seed

    def propagate_quenching_uncertainty(
        self,
        history: ThermalHistory
    ) -> Dict[str, UncertaintySummary]:
        """Propagate composition uncertainties through Quenching to Hardness, Ms, and Strength."""
        np.random.seed(self.seed)

        # Sample composition within ASTM A29 ranges
        c_samples = np.random.normal(0.40, 0.012, self.num_samples)
        mn_samples = np.random.normal(0.85, 0.05, self.num_samples)
        cr_samples = np.random.normal(0.95, 0.06, self.num_samples)
        mo_samples = np.random.normal(0.20, 0.02, self.num_samples)

        ms_list = []
        hv_list = []
        uts_list = []

        for i in range(self.num_samples):
            # Sampled composition
            comp_sample = {
                "C": float(np.clip(c_samples[i], 0.38, 0.43)),
                "Mn": float(np.clip(mn_samples[i], 0.75, 1.00)),
                "Si": 0.25,
                "Cr": float(np.clip(cr_samples[i], 0.80, 1.10)),
                "Mo": float(np.clip(mo_samples[i], 0.15, 0.25)),
                "P": 0.02,
                "S": 0.02,
                "Fe": 97.31
            }
            sample_mat = SteelMaterial(name="AISI4140_Sample", composition=comp_sample)
            thermo = ThermodynamicModel(sample_mat)
            crit = thermo.compute_all()
            ms_list.append(crit.Ms)

            # Phase and property
            trans = PhaseTransformationEngine(sample_mat, crit)
            micro_eng = MicrostructureEngine(sample_mat)
            ms_state = micro_eng.evaluate_microstructure(history)
            mech_pred = MechanicalPropertyPredictor(sample_mat)
            mech = mech_pred.predict_all(ms_state)
            hv_list.append(mech.hardness_hv)
            uts_list.append(mech.uts_mpa)

        def _summarize(arr: list[float]) -> UncertaintySummary:
            a = np.array(arr)
            return UncertaintySummary(
                mean=round(float(np.mean(a)), 2),
                std=round(float(np.std(a)), 2),
                ci_95=(round(float(np.percentile(a, 2.5)), 2), round(float(np.percentile(a, 97.5)), 2)),
                p10=round(float(np.percentile(a, 10)), 2),
                p50=round(float(np.median(a)), 2),
                p90=round(float(np.percentile(a, 90)), 2),
                samples_count=len(a)
            )

        return {
            "Ms_c": _summarize(ms_list),
            "hardness_hv": _summarize(hv_list),
            "uts_mpa": _summarize(uts_list)
        }
