import os
import wave
import numpy as np
import soundfile as sf
import subprocess
from pyrnnoise import RNNoise

def process(wav_path: str, output_dir: str) -> str:
    """
    RNNoise pass — GRU-based neural noise suppression.
    Handles non-stationary noise (traffic, crowd, wind).
    Requires: mono, 48kHz, 16-bit PCM.
    We resample to 48kHz, run RNNoise, then resample back to 16kHz.
    """

    temp_48k   = os.path.join(output_dir, "step4a_48k.wav")
    temp_rnn   = os.path.join(output_dir, "step4b_rnnoise.wav")
    output_path = os.path.join(output_dir, "step4_rnnoise.wav")

    # --- Resample to 48kHz (RNNoise requirement) ---
    cmd_up = [
        "ffmpeg", "-y", "-i", wav_path,
        "-ar", "48000", "-ac", "1",
        "-sample_fmt", "s16",
        temp_48k
    ]
    r = subprocess.run(cmd_up, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"[rnnoise] Upsample failed:\n{r.stderr}")

    # --- Run RNNoise ---
    denoiser     = RNNoise(sample_rate=48000)
    speech_probs = []

    for prob in denoiser.denoise_wav(temp_48k, temp_rnn):
        speech_probs.append(prob)

    avg_speech = float(np.mean(speech_probs)) if speech_probs else 0.0
    print(f"[rnnoise] RNNoise done — avg speech probability: {avg_speech:.2f}")

    # --- Resample back to 16kHz ---
    cmd_down = [
        "ffmpeg", "-y", "-i", temp_rnn,
        "-ar", "16000", "-ac", "1",
        "-sample_fmt", "s16",
        output_path
    ]
    r2 = subprocess.run(cmd_down, capture_output=True, text=True)
    if r2.returncode != 0:
        raise RuntimeError(f"[rnnoise] Downsample failed:\n{r2.stderr}")

    print(f"[rnnoise] ✅ Resampled back to 16kHz → {output_path}")
    return output_path