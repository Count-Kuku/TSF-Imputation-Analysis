"""Prediction horizons shared by evaluation and research planning.

This module needs only pandas; importing it never loads a forecasting model.
"""
from enum import Enum

from pandas.tseries.frequencies import to_offset


class Term(Enum):
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"

    @property
    def multiplier(self) -> int:
        return {Term.SHORT: 1, Term.MEDIUM: 10, Term.LONG: 15}[self]


PRED_LENGTH_MAP = {"M": 12, "W": 8, "D": 30, "H": 48, "T": 48, "S": 60}


def maybe_reconvert_freq(freq: str) -> str:
    aliases = {"Y": "A", "YE": "A", "QE": "Q", "ME": "M", "MS": "M",
               "h": "H", "min": "T", "s": "S", "us": "U"}
    return aliases.get(freq, freq)


def compute_prediction_length(freq: str, term: Term = Term.SHORT) -> int:
    # Anchors (W-SUN etc.) and start/end month labels share the same horizon.
    base_frequency = maybe_reconvert_freq(to_offset(freq).name.split("-")[0])
    return term.multiplier * PRED_LENGTH_MAP.get(base_frequency, 48)
