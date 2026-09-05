"""
Confidence calibration (section 8 and the calibration table in 2B).

Confidence must always reflect evidence quality -- never be inflated to
appear certain. These bands are the single source of truth other modules
draw from so that RULE, AI, and FALLBACK diagnoses stay calibrated
consistently against each other.
"""
from __future__ import annotations

# Calibration bands (inclusive lower bound, exclusive upper bound except
# the top band, which is inclusive of 1.0).
EXPLICIT_STRUCTURED_EVIDENCE = (0.90, 1.00)   # known decline code / verified
                                               # transaction signal / unambiguous
                                               # customer statement
STRONG_MULTI_SIGNAL = (0.75, 0.89)            # multiple strong supporting
                                               # signals, minor uncertainty
MIXED_OR_CONFLICTING = (0.40, 0.74)           # mixed / partially conflicting
LIMITED_EVIDENCE = (0.10, 0.39)               # limited evidence, significant
                                               # uncertainty
INSUFFICIENT_EVIDENCE = (0.00, 0.09)          # effectively no evidence

# Concrete default confidence to assign within each band unless a module
# has a more specific reason to pick a different point in the band.
DEFAULT_EXPLICIT = 0.95
DEFAULT_STRONG_MULTI = 0.82
DEFAULT_MIXED = 0.55
DEFAULT_LIMITED = 0.25
DEFAULT_INSUFFICIENT = 0.05


def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def lower_for_conflict(confidence: float, penalty: float = 0.25) -> float:
    """Apply the mandatory confidence penalty when signals conflict
    (section 9, rule 4). Never allows confidence to land back in the
    'explicit structured evidence' band once a conflict has been
    detected."""
    reduced = clamp(confidence - penalty)
    return min(reduced, STRONG_MULTI_SIGNAL[1])


def lower_for_missing_data(confidence: float, penalty: float = 0.15) -> float:
    return clamp(confidence - penalty)


def band_for(confidence: float) -> str:
    if confidence >= EXPLICIT_STRUCTURED_EVIDENCE[0]:
        return "EXPLICIT_STRUCTURED_EVIDENCE"
    if confidence >= STRONG_MULTI_SIGNAL[0]:
        return "STRONG_MULTI_SIGNAL"
    if confidence >= MIXED_OR_CONFLICTING[0]:
        return "MIXED_OR_CONFLICTING"
    if confidence >= LIMITED_EVIDENCE[0]:
        return "LIMITED_EVIDENCE"
    return "INSUFFICIENT_EVIDENCE"
