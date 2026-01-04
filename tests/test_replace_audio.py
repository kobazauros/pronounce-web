import pytest
from unittest.mock import MagicMock, patch, mock_open
import sys
import os

# Adjust path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import replace_audio

def test_standardize_audio(mocker):
    # Mock AudioSegment
    mock_audio = MagicMock()
    mock_audio.frame_rate = 44100
    mock_audio.channels = 2
    mock_audio.max_dBFS = -10.0
    
    # Mock methods to return self (fluent interface)
    mock_audio.set_frame_rate.return_value = mock_audio
    mock_audio.set_channels.return_value = mock_audio
    mock_audio.apply_gain.return_value = mock_audio
    
    mocker.patch('replace_audio.AudioSegment.from_file', return_value=mock_audio)
    
    success = replace_audio.standardize_audio('test.mp3')
    
    assert success is True
    # Verify transformations
    mock_audio.set_frame_rate.assert_called_with(16000)
    mock_audio.set_channels.assert_called_with(1)
    mock_audio.apply_gain.assert_called() # Should be called with -1.0 - (-10.0) = 9.0
    mock_audio.export.assert_called_with('test.mp3', format='mp3', bitrate='128k')

def test_populate_words(mocker):
    mock_json = {"words": ["one", "two"]}
    m = mock_open(read_data='{"words": ["one", "two"]}')
    with patch('builtins.open', m):
        mocker.patch('json.load', return_value=mock_json)
        words = replace_audio.populate_words()
        assert words == ["one", "two"]

def test_download_audio_uk_preference(mocker):
    # Mock requests.get for Dictionary API
    mock_response = MagicMock()
    mock_response.json.return_value = [{
        "phonetics": [
            {"audio": "http://example.com/us.mp3"},
            {"audio": "http://example.com/uk.mp3-uk"}
        ]
    }]
    
    # Mock requests.get calls
    # 1st call: API, 2nd call: Audio Download (successful)
    mock_audio_response = MagicMock()
    mock_audio_response.content = b"audio_data"
    
    mocker.patch('requests.get', side_effect=[mock_response, mock_audio_response])
    
    # Mock open
    m = mock_open()
    
    # Mock standardize_audio to avoid dependency
    mock_standardize = mocker.patch('replace_audio.standardize_audio', return_value=True)
    
    with patch('builtins.open', m):
        success = replace_audio.download_audio("test")
    
    assert success is True
    # Verify it chose the UK version and downloaded it
    # Note: request.get was called twice. 
    # Check calls to see if 2nd call was the UK url
    calls = replace_audio.requests.get.call_args_list
    assert 'uk.mp3-uk' in calls[1][0][0]

def test_download_audio_fallback(mocker):
    # Mock requests.get for Dictionary API (Only US available)
    mock_response = MagicMock()
    mock_response.json.return_value = [{
        "phonetics": [
            {"audio": "http://example.com/us.mp3"}
        ]
    }]
    
    mock_audio_response = MagicMock()
    mock_audio_response.content = b"audio_data"
    
    mocker.patch('requests.get', side_effect=[mock_response, mock_audio_response])
    
    m = mock_open()
    mock_standardize = mocker.patch('replace_audio.standardize_audio', return_value=True)
    
    with patch('builtins.open', m):
        success = replace_audio.download_audio("test")
        
    assert success is True
    # Verify it downloaded the US version
    calls = replace_audio.requests.get.call_args_list
    assert 'us.mp3' in calls[1][0][0]

def test_download_audio_not_found(mocker):
    mock_response = MagicMock()
    mock_response.json.return_value = [{"phonetics": []}] # No audio
    mocker.patch('requests.get', return_value=mock_response)
    
    success = replace_audio.download_audio("test")
    assert success is False
