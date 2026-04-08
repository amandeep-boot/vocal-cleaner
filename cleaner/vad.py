import wave
import struct
import webrtcvad

def process(wav_path: str, aggressiveness: int = 2, merge_gap_ms: int = 500) -> list:
    """
    Reads a 16kHz mono 16-bit WAV file.
    Returns a list of (start_ms, end_ms) tuples of voiced speech regions.
    
    aggressiveness: 0 (lenient) to 3 (strict)
    merge_gap_ms  : gaps shorter than this between voiced segments get merged
    """

    vad = webrtcvad.Vad(aggressiveness)

    with wave.open(wav_path, 'rb') as wf:
        sample_rate   = wf.getframerate()
        num_channels  = wf.getnchannels()
        sample_width  = wf.getsampwidth()
        total_frames  = wf.getnframes()
        raw_audio     = wf.readframes(total_frames)

    # webrtcvad requires: mono, 16-bit, 16kHz
    if sample_rate != 16000 or num_channels != 1 or sample_width != 2:
        raise ValueError(
            f"[vad] Invalid format. Expected mono/16kHz/16-bit. "
            f"Got: {num_channels}ch / {sample_rate}Hz / {sample_width*8}-bit"
        )

    # frame = 20ms of audio
    frame_duration_ms = 20
    frame_size        = int(sample_rate * frame_duration_ms / 1000)  # 320 samples
    bytes_per_frame   = frame_size * sample_width                     # 640 bytes

    # split raw audio into 20ms frames
    frames = [
        raw_audio[i:i + bytes_per_frame]
        for i in range(0, len(raw_audio), bytes_per_frame)
        if len(raw_audio[i:i + bytes_per_frame]) == bytes_per_frame
    ]

    # classify each frame
    voiced_flags = []
    for frame in frames:
        try:
            is_voiced = vad.is_speech(frame, sample_rate)
        except Exception:
            is_voiced = False
        voiced_flags.append(is_voiced)

    # convert flags to (start_ms, end_ms) segments
    raw_segments = []
    in_speech    = False
    start_ms     = 0

    for i, flag in enumerate(voiced_flags):
        current_ms = i * frame_duration_ms
        if flag and not in_speech:
            start_ms  = current_ms
            in_speech = True
        elif not flag and in_speech:
            raw_segments.append((start_ms, current_ms))
            in_speech = False

    if in_speech:
        raw_segments.append((start_ms, len(voiced_flags) * frame_duration_ms))

    # merge segments where gap between them is < merge_gap_ms
    if not raw_segments:
        print("[vad]No speech detected. Check aggressiveness setting.")
        return []

    merged = [raw_segments[0]]
    for start, end in raw_segments[1:]:
        prev_start, prev_end = merged[-1]
        if (start - prev_end) < merge_gap_ms:
            merged[-1] = (prev_start, end)   # merge
        else:
            merged.append((start, end))

    total_speech_ms   = sum(e - s for s, e in merged)
    total_removed_ms  = len(voiced_flags) * frame_duration_ms - total_speech_ms

    print(f"[vad]  Found {len(merged)} speech segment(s)")
    print(f"[vad]    Speech  : {total_speech_ms / 1000:.2f}s")
    print(f"[vad]    Silence : {total_removed_ms / 1000:.2f}s will be removed")
    print(f"[vad]    Segments: {merged}")

    return merged
  