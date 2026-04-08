import json
import os
from datetime import datetime
from typing import Any, Dict
from cleaner import ingest, rnnoise_step, vad, trim, denoise, normalize

def run(input_path: str, output_dir: str):
    print(f"\n[pipeline] Starting vocal cleaner")
    print(f"[pipeline] Input  : {input_path}")
    print(f"[pipeline] Output : {output_dir}")

    os.makedirs(output_dir, exist_ok=True)

    report: Dict[str, Any] = {
        "input": input_path,
        "output_dir": output_dir,
        "timestamp": datetime.now().isoformat(),
        "stages": []
    }

    # --- stages will be plugged in here one by one ---

    # --- step 1 : Ingest ----
    ingested_path = ingest.process(input_path=input_path, output_dir=output_dir)
    report["stages"].append({"step":"Ingest", "output":ingested_path})

    # --- STEP 2: VAD ---
    segments = vad.process(ingested_path, aggressiveness=2, merge_gap_ms=500)
    report["stages"].append({"step": "vad", "segments": segments, "count": len(segments)})

    # --- STEP 3: Trim ---
    trimmed_path, trim_stats = trim.process(ingested_path, segments, output_dir)
    report["stages"].append({"step": "trim", "output": trimmed_path, **trim_stats})

    # --- STEP 4: Denoise ---
    denoised_path = denoise.process(trimmed_path, output_dir)
    report["stages"].append({"step": "denoise", "output": denoised_path})

    # # --- STEP 5: Post-Denoise (additional cleanup) ---
    # final_denoised_path = denoise_post.process(denoised_path, output_dir)
    # report["stages"].append({"step": "denoise_post", "output": final_denoised_path})
    # --- STEP 5: RNNoise (non-stationary) ---
    rnn_path = rnnoise_step.process(denoised_path, output_dir)
    report["stages"].append({"step": "rnnoise", "output": rnn_path})

    # --- STEP 6: Normalize (always last) ---
    final_path, norm_stats = normalize.process(rnn_path, output_dir, target_lufs=-16.0)
    report["stages"].append({"step": "normalize", "output": final_path, **norm_stats})

    report["final_output"] = final_path

    report_path = os.path.join(output_dir, "report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"[pipeline] Done. Report saved → {report_path}\n")