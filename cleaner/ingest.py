import subprocess
import os

def process(input_path: str, output_dir: str) -> str :
  output_path = os.path.join(output_dir,"step1_ingest.wav")

  command = [
    "ffmpeg", "-y",
    "-i", input_path,
    "-af", "highpass=f=160",
    "-ac", "1",
    "-ar", "16000",
    "-sample_fmt", "s16",
    output_path
  ]

  result = subprocess.run(command, capture_output=True, text=True)

  if result.returncode != 0:
    raise RuntimeError(f"[ingest] FFmpeg failed:\n{result.stderr}")
  
  print(f"[ingest] Converted to mono 16kHz WAV -> {output_path}")
  return output_path