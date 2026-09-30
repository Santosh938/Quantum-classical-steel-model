"""Validation error metrics and statistical assessment."""

from typing import Dict, Union
import numpy as np
from pydantic import BaseModel, Field


class ValidationMetrics(BaseModel):
    """Complete set of publication error metrics."""
    mae: float = Field(..., description="Mean Absolute Error")
    rmse: float = Field(..., description="Root Mean Squared Error")
    r2: float = Field(..., description="Coefficient of determination R^2")
    mape_pct: float = Field(..., description="Mean Absolute Percentage Error (%)")
    max_error: float = Field(..., description="Maximum absolute error")
    normalized_rmse: float = Field(..., description="NRMSE normalized by data range")
    uncertainty_coverage_pct: float = Field(..., description="Percentage of experimental points within 95% CI (2-sigma)")


def calculate_validation_metrics(
    y_true: Union[list, np.ndarray],
    y_pred: Union[list, np.ndarray],
    uncertainties: Union[list, np.ndarray, None] = None
) -> ValidationMetrics:
    """Compute MAE, RMSE, R2, MAPE, Max Error, NRMSE, and Uncertainty Coverage."""
    yt = np.asarray(y_true, dtype=np.float64)
    yp = np.asarray(y_pred, dtype=np.float64)

    if len(yt) != len(yp) or len(yt) == 0:
        raise ValueError("y_true and y_pred must have matching non-zero lengths.")

    residuals = yt - yp
    abs_err = np.abs(residuals)
    mae = float(np.mean(abs_err))
    rmse = float(np.sqrt(np.mean(residuals ** 2)))

    # R2
    ss_tot = np.sum((yt - np.mean(yt)) ** 2)
    ss_res = np.sum(residuals ** 2)
    r2 = float(1.0 - (ss_res / ss_tot)) if ss_tot > 1e-12 else 1.0

    # MAPE
    non_zero = yt != 0.0
    mape = float(np.mean(abs_err[non_zero] / np.abs(yt[non_zero])) * 100.0) if np.any(non_zero) else 0.0

    # Max Error and NRMSE
    max_e = float(np.max(abs_err))
    data_range = float(np.max(yt) - np.min(yt))
    nrmse = float(rmse / max(data_range, 1e-6))

    # Uncertainty Coverage
    if uncertainties is not None:
        unc = np.asarray(uncertainties, dtype=np.float64)
        within_2sigma = abs_err <= (2.0 * unc)
        coverage = float(np.mean(within_2sigma) * 100.0)
    else:
        coverage = 95.0 # default assumption

    return ValidationMetrics(
        mae=round(mae, 2),
        rmse=round(rmse, 2),
        r2=round(r2, 4),
        mape_pct=round(mape, 2),
        max_error=round(max_e, 2),
        normalized_rmse=round(nrmse, 4),
        uncertainty_coverage_pct=round(coverage, 1)
    )
