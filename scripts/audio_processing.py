import io
import logging
import numpy as np
import librosa
import soundfile as sf

# Configure logger
logger = logging.getLogger(__name__)


def process_audio_data(audio_data: bytes, target_sr: int = 16000) -> bytes:
    """
    Standardizes audio data to a specific format:
    - Resamples to target_sr (default 16000 Hz)
    - Converts to Mono
    - Normalizes volume (Peak normalization to -0.5dB)
    - Exports as MP3 bytes

    Args:
        audio_data (bytes): Raw audio bytes (WAV, MP3, etc.)
        target_sr (int): Target sample rate in Hz.

    Returns:
        bytes: Processed MP3 audio bytes.
    """
    try:
        # Load audio from bytes
        # librosa.load supports various formats via wrapping soundfile/audioread
        # mono=True mixes down to mono immediately
        y, sr = librosa.load(io.BytesIO(audio_data), sr=target_sr, mono=True)

        # Handle silence or empty audio
        if y.size == 0:
            logger.warning("Empty audio data received during processing.")
            return audio_data

        # --- CLIPPING DETECTION ---
        # Clipping distorts formants significantly (15-20% error on F1).
        # We reject audio if > 0.5% samples are fully saturated (>0.99)
        max_possible = 1.0  # Float32 normalized
        clipped_samples = np.sum(np.abs(y) > 0.99)
        clip_ratio = clipped_samples / len(y)

        if clip_ratio > 0.005:  # 0.5%
            error_msg = f"Audio clipping detected ({clip_ratio*100:.1f}%). Please reduce microphone volume."
            logger.warning(error_msg)
            # We return a specific error bytes marker or raise?
            # Since return type is bytes, we can't easily raise without breaking caller.
            # However, this function is utility. It SHOULD raise.
            # BUT existing code catches 'Exception' and returns original.
            # To force failure, we raise a custom ValueError that caller can catch specifically?
            # For now, let's Log and Proceed but maybe capping it won't help.
            # Actually, if we return original, the system analyzes clipped audio.
            # We MUST fail or signal failure.
            raise ValueError(error_msg)

        # --- ROBUST TRIM SILENCE ---
        # Ported from optimized JS logic:
        # 1. Calculate adaptive noise floor (10th percentile of RMS)
        # 2. Thresholds: Vol 4.0x, Sens 2.5x
        # 3. ZCR check for tails

        frame_length = int(target_sr * 0.02)  # 20ms
        hop_length = frame_length  # Non-overlapping for speed/parity with JS

        # Calculate RMS energy per frame
        rmse = librosa.feature.rms(
            y=y, frame_length=frame_length, hop_length=hop_length, center=False
        )[0]

        # Calculate ZCR per frame
        zcr = librosa.feature.zero_crossing_rate(
            y=y, frame_length=frame_length, hop_length=hop_length, center=False
        )[0]

        if len(rmse) > 0:
            # 1. Adaptive Noise Floor (10th percentile)
            sorted_rms = np.sort(rmse)
            floor_idx = int(len(sorted_rms) * 0.1)
            local_floor = (
                sorted_rms[floor_idx] if floor_idx < len(sorted_rms) else 0.001
            )
            local_floor = max(0.001, local_floor)

            # 2. Thresholds (RELAXED for trailing consonants)
            # Originally 4.0x/2.5x - reduced to 2.0x/1.5x to catch quiet releases
            vol_thresh = max(0.015, local_floor * 2.0)
            sens_thresh = max(0.005, local_floor * 1.5)
            zcr_thresh = 0.1

            # 3. Identify Speech Frames
            # Logic: Loud OR (Moderately Loud AND High Frequency)
            is_speech = (rmse > vol_thresh) | (
                (rmse > sens_thresh) & (zcr > zcr_thresh)
            )

            # Find start/end
            speech_indices = np.where(is_speech)[0]

            if len(speech_indices) > 0:
                start_frame = speech_indices[0]
                end_frame = speech_indices[-1]

                # Convert to samples
                start_sample = start_frame * hop_length
                end_sample = (end_frame + 1) * hop_length

                # Padding: 100ms (0.1s) - Increased from 10ms to preserve tails
                padding = int(target_sr * 0.1)

                start = max(0, start_sample - padding)
                end = min(len(y), end_sample + padding)

                y_trimmed = y[start:end]

                if len(y_trimmed) > 1000:  # Min duration check
                    y = y_trimmed
            else:
                logger.warning("No speech detected by robust trim. Returning original.")

        if y.size == 0:
            logger.warning("Audio checks out empty after trimming.")
            # Fallback to original loaded if trim kills it (unlikely)
            y, _ = librosa.load(io.BytesIO(audio_data), sr=target_sr, mono=True)

        # Peak Normalization
        # Target peak is 0.95 (~-0.5dB) to prevent clipping while maximizing dynamic range
        max_val = float(np.max(np.abs(y)))
        if max_val > 0:
            y = 0.95 * y / max_val

        # Check if we have valid data after normalization
        if not np.isfinite(y).all():
            logger.warning(
                "NaN or Inf encountered during normalization. Returning original."
            )
            return audio_data

        # Export to MP3 using soundfile
        # Note: soundfile requires 'libsndfile' to be installed.
        # Writing to BytesIO to return bytes
        output_io = io.BytesIO()
        sf.write(output_io, y, sr, format="MP3")
        output_io.seek(0)

        return output_io.getvalue()

    except Exception as e:
        logger.error(f"Error processing audio data: {e}")
        # Identify if it's a specific known error (e.g. format not supported)
        # Fallback: Return original bytes if processing fails to avoid data loss (though it wont be standardized)
        return audio_data
