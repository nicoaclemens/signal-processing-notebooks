# used by: cells\filter_chain\processing.py, cells\filter_chain\ui.py
import io
import wave
import base64

import numpy as np


def _to_float_mono(raw_bytes, channels, sampwidth):
    if sampwidth == 1:
        data = np.frombuffer(raw_bytes, dtype=np.uint8).astype(np.float32)
        data = (data - 128.0) / 128.0
    elif sampwidth == 2:
        data = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32)
        data = data / 32768.0
    elif sampwidth == 3:
        b = np.frombuffer(raw_bytes, dtype=np.uint8).reshape(-1, 3)
        i32 = (
            b[:, 0].astype(np.int32)
            | (b[:, 1].astype(np.int32) << 8)
            | (b[:, 2].astype(np.int32) << 16)
        )
        sign = i32 & 0x800000
        i32 = i32 - (sign << 1)
        data = i32.astype(np.float32) / 8388608.0
    elif sampwidth == 4:
        data = np.frombuffer(raw_bytes, dtype=np.int32).astype(np.float32)
        data = data / 2147483648.0
    else:
        raise ValueError(f"Unsupported WAV sample width: {sampwidth} bytes")

    if channels > 1:
        data = data.reshape(-1, channels).mean(axis=1)

    return data


def load_wav_from_upload(upload_value):
    if not upload_value:
        return None

    if isinstance(upload_value, dict):
        entry = next(iter(upload_value.values()), None)
    else:
        entry = upload_value[0] if len(upload_value) else None

    if not entry:
        return None

    name = entry.get("name", "uploaded.wav")
    content = entry.get("content")
    if content is None:
        return None

    if isinstance(content, memoryview):
        content = content.tobytes()
    else:
        content = bytes(content)

    with wave.open(io.BytesIO(content), "rb") as wf:
        channels = wf.getnchannels()
        sample_width = wf.getsampwidth()
        sample_rate = wf.getframerate()
        frame_count = wf.getnframes()
        raw = wf.readframes(frame_count)

    samples = _to_float_mono(raw, channels, sample_width)
    if samples.size == 0:
        raise ValueError("Uploaded WAV file is empty")

    samples = samples - np.mean(samples)
    max_abs = np.max(np.abs(samples))
    if max_abs > 0:
        samples = samples / max_abs

    duration_s = float(len(samples)) / float(sample_rate)

    return {
        "name": name,
        "sample_rate": int(sample_rate),
        "samples": samples,
        "duration_s": duration_s,
    }


def resample_for_periodic_source(samples, target_len):
    samples = np.asarray(samples, dtype=float)
    if samples.size == 0:
        return np.zeros(target_len, dtype=float)

    src_x = np.linspace(0, 1, len(samples), endpoint=False)
    dst_x = np.linspace(0, 1, target_len, endpoint=False)
    out = np.interp(dst_x, src_x, samples)

    max_abs = np.max(np.abs(out))
    if max_abs > 0:
        out = out / max_abs

    return out


def signal_to_wav_data_uri(samples, sample_rate):
    samples = np.asarray(samples, dtype=np.float32)
    if samples.size == 0:
        samples = np.zeros(1, dtype=np.float32)

    clipped = np.clip(samples, -1.0, 1.0)
    pcm16 = (clipped * 32767.0).astype(np.int16)

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(int(sample_rate))
        wf.writeframes(pcm16.tobytes())

    b64 = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:audio/wav;base64,{b64}"


def build_audio_player_html(samples, sample_rate, loop=False, autoplay=False):
    src = signal_to_wav_data_uri(samples, sample_rate)
    loop_attr = " loop" if loop else ""
    autoplay_attr = " autoplay" if autoplay else ""
    return (
        '<audio controls preload="metadata" style="width:100%;"'
        f"{loop_attr}{autoplay_attr}>"
        f'<source src="{src}" type="audio/wav">'
        "Your browser does not support the audio element."
        "</audio>"
    )
