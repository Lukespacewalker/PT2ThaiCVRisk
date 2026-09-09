"""Pure Thai CV Risk Score calculations shared by the data pipeline."""

import math


def calc_thai_cv_risk(age, sex, sbp, dm, chol, smoking=0):
    """Calculate the 10-year Thai CV Risk using the cholesterol model."""
    if any(value is None for value in (age, sex, sbp, dm, chol, smoking)):
        return None
    full_score = (
        (0.08183 * age)
        + (0.39499 * sex)
        + (0.02084 * sbp)
        + (0.69974 * dm)
        + (0.00212 * chol)
        + (0.41916 * smoking)
    )
    risk = (1.0 - math.pow(0.978296, math.exp(full_score - 7.04423))) * 100.0
    return round(max(0.0, risk), 2)


def get_extrapolation_reasons(age, sbp, chol):
    """Return model inputs outside the published Thai CV Risk ranges."""
    reasons = []
    if age is not None and not 35 <= age <= 70:
        reasons.append("age")
    if sbp is not None and not 80 <= sbp <= 200:
        reasons.append("sbp")
    if chol is not None and not 150 <= chol <= 280:
        reasons.append("cholesterol")
    return reasons
