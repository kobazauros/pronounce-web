import pytest
from unittest.mock import MagicMock, patch, mock_open
import sys
import os
import numpy as np

# Adjust path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import analyze_vowels

def test_load_audio_mono(mocker):
    # Mock librosa
    mock_librosa = mocker.patch('analyze_vowels.librosa')
    mock_librosa.load.return_value = (np.array([0.1, 0.2]), 22050)
    mock_librosa.resample.return_value = np.array([0.1, 0.2])
    
    # Run
    y, sr = analyze_vowels.load_audio_mono(MagicMock(as_posix=lambda: "test.mp3"), target_sr=16000)
    
    assert sr == 16000
    mock_librosa.resample.assert_called_once()
    assert y.dtype == np.float32

def test_find_syllable_nucleus(mocker):
    mock_sound = MagicMock()
    mock_pitch = mock_sound.to_pitch.return_value
    
    # Setup pitch frames: 3 frames, middle one voiced
    mock_pitch.get_number_of_frames.return_value = 3
    mock_pitch.get_value_in_frame.side_effect = [0, 100, 0, 0] # 1-indexed in code logic usually
    mock_pitch.get_time_from_frame_number.side_effect = lambda x: x * 0.1
    
    mock_intensity = mock_sound.to_intensity.return_value
    mock_intensity.get_maximum.return_value = 80.0
    
    # We need to adjust side_effect to match the loop in code:
    # for i in range(1, n_frames + 1): get_value_in_frame(i)
    mock_pitch.get_value_in_frame.side_effect = [0, 100, 0] 
    
    # Run
    result = analyze_vowels.find_syllable_nucleus(mock_sound)
    
    # Logic is intricate, but if mocked correctly it should find the middle segment
    # Time 1 (0.1s) -> unvoiced
    # Time 2 (0.2s) -> voiced (start)
    # Time 3 (0.3s) -> unvoiced (end)
    # Segment: 0.2 to 0.3. Duration 0.1s > 0.03s threshold.
    assert result == pytest.approx((0.2, 0.3))

def test_measure_formants(mocker):
    mock_sound = MagicMock()
    mock_formant = mock_sound.to_formant_burg.return_value
    
    # Mock get_value_at_time
    mock_formant.get_value_at_time.side_effect = [500, 1500] # F1, F2
    
    segment = (0.0, 1.0)
    results = analyze_vowels.measure_formants(mock_sound, segment, points=(0.5,))
    
    assert len(results) == 1
    assert results[0] == (500, 1500)

def test_analyze_file_pair(mocker):
    # Mock EVERYTHING
    mocker.patch('analyze_vowels.load_audio_mono', return_value=(np.array([]), 16000))
    mocker.patch('analyze_vowels.parselmouth.Sound')
    mocker.patch('analyze_vowels.find_syllable_nucleus', return_value=(0, 1))
    
    # Mock measure_formants to return known values
    # Student: (500, 1500)
    # Reference: (510, 1510)
    # Diff: 10, 10 -> hypot(10, 10) ~= 14.14
    mocker.patch('analyze_vowels.measure_formants', side_effect=[[(500, 1500)], [(510, 1510)]])
    
    word_info = {"type": "monophthong"}
    
    res = analyze_vowels.analyze_file_pair(MagicMock(), MagicMock(), word_info)
    
    assert res['F1'] == 500
    assert res['F2'] == 1500
    assert 14.0 < res['distance'] < 14.2

def test_load_map_json(mocker):
    m = mock_open(read_data='{"words": [{"word": "Test", "target": "e"}]}')
    with patch('builtins.open', m):
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mapping = analyze_vowels.load_map_json(mock_path)
        
    assert "test" in mapping
    assert mapping["test"]["target"] == "e"
