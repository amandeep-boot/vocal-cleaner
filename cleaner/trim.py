import os
from pydub import AudioSegment

def process(wav_path: str, segments: list, output_dir: str, min_segment_ms: int = 300) -> str:
    """
    Cuts the WAV file to only the voiced segments detected by VAD.
    Skips segments shorter than min_segment_ms (likely noise blips).
    Stitches all kept segments together into one clean WAV.
    """

    output_path = os.path.join(output_dir, "step2_trimmed.wav")

    audio = AudioSegment.from_wav(wav_path)

    kept_segments  = []
    skipped_count  = 0
    total_kept_ms  = 0
    total_duration = len(audio)

    for start_ms, end_ms in segments:
        duration = end_ms - start_ms

        if duration < min_segment_ms:
            print(f"[trim]   Skipping short segment ({start_ms}ms → {end_ms}ms, {duration}ms)")
            skipped_count += 1
            continue

        # safety clamp — don't exceed actual audio length
        end_ms = min(end_ms, total_duration)
        kept_segments.append(audio[start_ms:end_ms])
        total_kept_ms += duration

    if not kept_segments:
        raise RuntimeError("[trim] No segments passed the minimum duration filter. Try lowering min_segment_ms.")

    # stitch all kept segments together
    trimmed_audio = kept_segments[0]
    for seg in kept_segments[1:]:
        trimmed_audio += seg

    trimmed_audio.export(output_path, format="wav")

    total_removed_ms = total_duration - total_kept_ms
    print(f"[trim]    Trimmed audio saved → {output_path}")
    print(f"[trim]    Original : {total_duration / 1000:.2f}s")
    print(f"[trim]    Kept     : {total_kept_ms / 1000:.2f}s")
    print(f"[trim]    Removed  : {total_removed_ms / 1000:.2f}s of silence")
    print(f"[trim]    Skipped  : {skipped_count} short segment(s)")

    return output_path, {
        "original_duration_s": round(total_duration / 1000, 2),
        "kept_duration_s"    : round(total_kept_ms / 1000, 2),
        "removed_duration_s" : round(total_removed_ms / 1000, 2),
        "skipped_segments"   : skipped_count
    }