from typing import TYPE_CHECKING, assert_type
import static_ffmpeg
import parselmouth

if TYPE_CHECKING:
    # 1. Check static_ffmpeg
    assert_type(static_ffmpeg.add_paths(), bool)
    
    # 2. Check parselmouth
    assert_type(parselmouth.Sound, type[parselmouth.Sound])
    
    # Check return types of common methods
    s = parselmouth.Sound("dummy.wav")
    assert_type(s.to_pitch(), parselmouth.Pitch)
    assert_type(s.to_intensity(), parselmouth.Intensity)
    assert_type(s.get_intensity(), float)

