# pyright: strict
import numpy as np
from analysis_engine import (
    hz_to_bark,
    get_vowel_type,
    get_articulatory_feedback,
    calculate_distance,
)


def test_hz_to_bark():
    """Verify frequency to Bark conversion math."""
    # Standard human voice range values
    # 26.81 * 500 / (1960 + 500) - 0.53 = 4.919...
    assert round(hz_to_bark(500), 2) == 4.92
    # 26.81 * 1500 / (1960 + 1500) - 0.53 = 11.092...
    assert round(hz_to_bark(1500), 2) == 11.09

    # Edge cases
    assert np.isnan(hz_to_bark(0))
    assert np.isnan(hz_to_bark(-100))
    assert np.isnan(hz_to_bark(np.nan))


def test_get_vowel_type():
    """Test monophthong vs diphthong logic."""
    assert get_vowel_type("iː") == "monophthong"
    assert get_vowel_type("uː") == "monophthong"
    assert get_vowel_type("aɪ") == "diphthong"
    assert get_vowel_type("əʊ") == "diphthong"
    assert get_vowel_type("eə") == "diphthong"
    # Word with parens in label
    assert get_vowel_type("(æ)") == "monophthong"


def test_get_articulatory_feedback_f1():
    """Test jaw/height feedback logic (F1)."""
    # Ref F1 = 500
    # Stud F1 = 400 (Difference -100 < -50 Thresh) -> Open more
    assert "Open mouth more" in get_articulatory_feedback(400, 1500, 500, 1500)

    # Stud F1 = 600 (Difference 100 > 50 Thresh) -> Close slightly
    assert "Close mouth slightly" in get_articulatory_feedback(600, 1500, 500, 1500)

    # Stud F1 = 520 (Difference 20 < 50 Thresh) -> Empty
    assert get_articulatory_feedback(520, 1500, 500, 1500) == ""


def test_get_articulatory_feedback_f2():
    """Test tongue backness feedback logic (F2)."""
    # Ref F2 = 2000
    # Stud F2 = 1800 (Diff -200 < -100 Thresh) -> Move forward
    assert "Move tongue forward" in get_articulatory_feedback(500, 1800, 500, 2000)

    # Stud F2 = 2200 (Diff 200 > 100 Thresh) -> Move back
    assert "Move tongue back" in get_articulatory_feedback(500, 2200, 500, 2000)


def test_calculate_distance_basic():
    """Verify Euclidean distance math for both Hz and Bark."""
    meas_s = [(500.0, 1500.0)]
    meas_r = [(500.0, 1500.0)]
    hz, bark = calculate_distance(meas_s, meas_r, alpha=1.0)
    assert hz == 0.0
    assert bark == 0.0


def test_calculate_distance_with_alpha():
    """Ensure Scaling Factor (Alpha) is applied correctly."""
    # Alpha = 1.1 means student formants are divided by 1.1
    # StudRaw = 550.0, 1650.0 -> StudNorm = 500.0, 1500.0
    # Ref = 500.0, 1500.0
    # Distance should be 0
    meas_s = [(550.0, 1650.0)]
    meas_r = [(500.0, 1500.0)]
    hz, bark = calculate_distance(meas_s, meas_r, alpha=1.1)
    assert round(hz, 2) == 0.0
    assert round(bark, 2) == 0.0


def test_calculate_distance_nan_handling():
    """Distance should handle NaNs gracefully."""
    meas_s = [(np.nan, 1500.0)]
    meas_r = [(500.0, 1500.0)]
    hz, bark = calculate_distance(meas_s, meas_r, alpha=1.0)
    assert np.isnan(hz)
    assert np.isnan(bark)
