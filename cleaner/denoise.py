import os
import subprocess
import numpy as np
import soundfile as sf
import noisereduce as nr

def process(wav_path: str, output_dir: str) -> str:

    pass1_path  = os.path.join(output_dir, "step3a_afftdn.wav")
    output_path = os.path.join(output_dir, "step3_denoised.wav")

    # --- Pass 1: FFmpeg afftdn (FFT-based denoiser) ---
    # profiles noise from first 0.5s, then applies 97dB reduction
    command = [
        "ffmpeg", "-y",
        "-i", wav_path,
        "-af",
        "asendcmd=c='0.0 afftdn@dn sn start\\; 0.5 afftdn@dn sn stop',"
        "afftdn@dn=nr=97:nf=-60:tn=1",  # lowered noise floor from -50 to -60
        pass1_path
    ]

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"[denoise] ⚠️  afftdn failed, falling back to noisereduce only")
        print(result.stderr[-300:])
        pass1_path = wav_path   # skip pass 1, use original

    else:
        print(f"[denoise] ✅ Pass 1 (afftdn) done → {pass1_path}")

    # --- Pass 2: noisereduce stationary ---
    audio, sample_rate = sf.read(pass1_path)

    if audio.dtype != np.float32:
        audio = audio.astype(np.float32)

    noise_sample = _extract_noise_sample(audio, int(sample_rate * 0.5))

    reduced = nr.reduce_noise(
        y=audio,
        sr=sample_rate,
        y_noise=noise_sample,
        prop_decrease=1.0,
        stationary=True,
        n_fft=512,
        n_std_thresh_stationary=1.2,
        freq_mask_smooth_hz=200,
        time_mask_smooth_ms=50
    )

    # --- Pass 3: noisereduce non-stationary ---
    reduced = nr.reduce_noise(
        y=reduced,
        sr=sample_rate,
        stationary=False,
        prop_decrease=0.9,
        n_fft=512,
        time_constant_s=0.5,
        thresh_n_mult_nonstationary=1.5,
        sigmoid_slope_nonstationary=10
    )

    sf.write(output_path, reduced, sample_rate)
    print(f"[denoise] ✅ Pass 2 (stationary) + Pass 3 (non-stationary) done → {output_path}")

    return output_path


def _extract_noise_sample(audio: np.ndarray, window_size: int) -> np.ndarray:
    if len(audio) < window_size:
        return audio
    min_rms    = float("inf")
    best_start = 0
    step       = window_size // 2
    for start in range(0, len(audio) - window_size, step):
        window = audio[start: start + window_size]
        rms    = float(np.sqrt(np.mean(window ** 2)))
        if rms < min_rms:
            min_rms    = rms
            best_start = start
    return audio[best_start: best_start + window_size]