import os
import subprocess

def process(wav_path: str, output_dir: str, target_lufs: float = -16.0) -> str:
    """
    Two-pass EBU R128 loudness normalization using FFmpeg loudnorm.
    Pass 1 — measures the actual loudness of the file.
    Pass 2 — applies correction to hit the target LUFS exactly.
    -16 LUFS is standard for music vocals.
    -1 dBTP true peak ceiling prevents clipping.
    """

    output_path = os.path.join(output_dir, "step5_normalized.wav")

    # --- Pass 1: measure loudness ---
    measure_cmd = [
        "ffmpeg", "-y",
        "-i", wav_path,
        "-af", f"loudnorm=I={target_lufs}:TP=-1:LRA=11:print_format=json",
        "-f", "null", "-"
    ]

    result = subprocess.run(measure_cmd, capture_output=True, text=True)

    # loudnorm stats come in stderr
    stderr = result.stderr
    stats  = _parse_loudnorm_stats(stderr)

    if not stats:
        print("[normalize] ⚠️  Could not parse loudnorm stats, running single-pass")
        stats = {}

    # --- Pass 2: apply correction ---
    measured_I   = stats.get("input_i",   "-99.0")
    measured_TP  = stats.get("input_tp",  "-99.0")
    measured_LRA = stats.get("input_lra", "0.0")
    measured_thresh = stats.get("input_thresh", "-99.0")

    normalize_cmd = [
        "ffmpeg", "-y",
        "-i", wav_path,
        "-af",
        f"loudnorm=I={target_lufs}:TP=-1:LRA=11"
        f":measured_I={measured_I}"
        f":measured_TP={measured_TP}"
        f":measured_LRA={measured_LRA}"
        f":measured_thresh={measured_thresh}"
        f":linear=true:print_format=summary",
        output_path
    ]

    result2 = subprocess.run(normalize_cmd, capture_output=True, text=True)

    if result2.returncode != 0:
        raise RuntimeError(f"[normalize] FFmpeg failed:\n{result2.stderr}")

    print(f"[normalize] ✅ Normalized → {output_path}")
    print(f"[normalize]    Target  : {target_lufs} LUFS")
    print(f"[normalize]    Input was: {measured_I} LUFS")
    print(f"[normalize]    Peak ceiling: -1 dBTP")

    return output_path, {
        "target_lufs"  : target_lufs,
        "input_lufs"   : measured_I,
        "true_peak_ceiling": -1.0
    }


def _parse_loudnorm_stats(stderr: str) -> dict:
    """Extracts loudnorm JSON stats from FFmpeg stderr."""
    import json
    try:
        start = stderr.rfind("{")
        end   = stderr.rfind("}") + 1
        if start == -1 or end == 0:
            return {}
        return json.loads(stderr[start:end])
    except Exception:
        return {}