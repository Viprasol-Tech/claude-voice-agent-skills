#!/usr/bin/env python3
"""Telephony audio toolkit: G.711 mu-law <-> PCM16, resampling, WAV I/O and frame maths.

Part of claude-voice-agent-skills by Viprasol Tech Private Limited.

Python 3.13 removed the `audioop` module (PEP 594), which many voice-agent
tutorials still use for mu-law. This file implements G.711 mu-law directly with
the standard library, so it works on every Python from 3.10 up.

  python voice_audio.py info call.wav
  python voice_audio.py to-mulaw input.wav out.ulaw          # resamples to 8 kHz mono first
  python voice_audio.py from-mulaw in.ulaw out.wav --rate 16000
  python voice_audio.py frames --rate 8000 --ms 20 --codec mulaw
  python voice_audio.py --self-test
"""

from __future__ import annotations

import argparse
import array
import math
import sys
import wave

BIAS = 0x84   # 132
CLIP = 32635


def mulaw_encode_sample(sample: int) -> int:
    """One 16-bit signed PCM sample -> one G.711 mu-law byte."""
    sign = 0x80 if sample < 0 else 0
    if sample < 0:
        sample = -sample
    sample = min(sample, CLIP) + BIAS
    exponent = 7
    mask = 0x4000
    while exponent > 0 and not (sample & mask):
        exponent -= 1
        mask >>= 1
    mantissa = (sample >> (exponent + 3)) & 0x0F
    return ~(sign | (exponent << 4) | mantissa) & 0xFF


def mulaw_decode_sample(byte: int) -> int:
    """One G.711 mu-law byte -> one 16-bit signed PCM sample."""
    byte = ~byte & 0xFF
    sign = byte & 0x80
    exponent = (byte >> 4) & 0x07
    mantissa = byte & 0x0F
    sample = ((mantissa << 3) + BIAS) << exponent
    sample -= BIAS
    return -sample if sign else sample


_DECODE_TABLE = [mulaw_decode_sample(b) for b in range(256)]


def mulaw_encode(pcm16: bytes) -> bytes:
    """Little-endian PCM16 bytes -> mu-law bytes."""
    samples = array.array("h")
    samples.frombytes(pcm16)
    if sys.byteorder == "big":
        samples.byteswap()
    return bytes(mulaw_encode_sample(s) for s in samples)


def mulaw_decode(data: bytes) -> bytes:
    """mu-law bytes -> little-endian PCM16 bytes."""
    samples = array.array("h", (_DECODE_TABLE[b] for b in data))
    if sys.byteorder == "big":
        samples.byteswap()
    return samples.tobytes()


def _lowpass_taps(cutoff: float, taps: int = 63) -> list[float]:
    """Windowed-sinc (Blackman) low-pass FIR; cutoff as a fraction of the sample rate (0-0.5)."""
    mid = (taps - 1) / 2
    h = []
    for n in range(taps):
        x = n - mid
        sinc = 2 * cutoff if x == 0 else math.sin(2 * math.pi * cutoff * x) / (math.pi * x)
        window = 0.42 - 0.5 * math.cos(2 * math.pi * n / (taps - 1)) + 0.08 * math.cos(4 * math.pi * n / (taps - 1))
        h.append(sinc * window)
    total = sum(h)
    return [v / total for v in h]


def _filter(samples: array.array, taps: list[float]) -> list[float]:
    half = len(taps) // 2
    n = len(samples)
    out = [0.0] * n
    for i in range(n):
        acc = 0.0
        for k, c in enumerate(taps):
            j = i + k - half
            if 0 <= j < n:
                acc += c * samples[j]
        out[i] = acc
    return out


def resample(pcm16: bytes, src_rate: int, dst_rate: int) -> bytes:
    """Resample a WHOLE buffer of mono PCM16 (little-endian).

    Downsampling first applies a windowed-sinc low-pass at the new Nyquist
    frequency, so 24 kHz or 16 kHz TTS output can be taken to 8 kHz without
    aliasing; then linear interpolation at position i * src_rate / dst_rate.
    Not for chunk-by-chunk streaming (filter state and phase are not carried
    between calls): for live streams use soxr, libsamplerate, or audioop-lts
    ratecv with its state.
    ponytail: pure-Python O(n * 63) filter; use numpy/soxr for long files.
    """
    if src_rate <= 0 or dst_rate <= 0:
        raise ValueError("sample rates must be positive")
    if src_rate == dst_rate:
        return pcm16
    src = array.array("h")
    src.frombytes(pcm16[: len(pcm16) - len(pcm16) % 2])
    if sys.byteorder == "big":
        src.byteswap()
    if not src:
        return b""
    data: list[float] | array.array = src
    if dst_rate < src_rate:
        data = _filter(src, _lowpass_taps(0.45 * dst_rate / src_rate))
    n_out = max(1, round(len(src) * dst_rate / src_rate))
    ratio = src_rate / dst_rate
    last = len(src) - 1
    out = array.array("h", [0] * n_out)
    for i in range(n_out):
        pos = min(i * ratio, last)
        j = int(pos)
        frac = pos - j
        a = data[j]
        b = data[min(j + 1, last)]
        out[i] = max(-32768, min(32767, int(round(a + (b - a) * frac))))
    if sys.byteorder == "big":
        out.byteswap()
    return out.tobytes()


def to_mono(pcm16: bytes, channels: int) -> bytes:
    if channels == 1:
        return pcm16
    s = array.array("h")
    s.frombytes(pcm16[: len(pcm16) - len(pcm16) % 2])
    if sys.byteorder == "big":
        s.byteswap()
    usable = len(s) - len(s) % channels  # drop a trailing partial frame
    mono = array.array("h", (int(sum(s[i:i + channels]) / channels) for i in range(0, usable, channels)))
    if sys.byteorder == "big":
        mono.byteswap()
    return mono.tobytes()


def frame_bytes(rate: int, ms: int, codec: str) -> int:
    """Bytes per frame: 20 ms of 8 kHz mu-law = 160 bytes; 20 ms of 16 kHz PCM16 = 640 bytes."""
    samples = rate * ms // 1000
    return samples * (1 if codec in ("mulaw", "alaw") else 2)


def read_wav(path: str) -> tuple[bytes, int, int]:
    with wave.open(path, "rb") as w:
        if w.getsampwidth() != 2:
            raise ValueError(f"{path}: expected 16-bit PCM WAV, got {8 * w.getsampwidth()}-bit")
        return w.readframes(w.getnframes()), w.getframerate(), w.getnchannels()


def write_wav(path: str, pcm16: bytes, rate: int) -> None:
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm16)


def _self_test() -> None:
    assert mulaw_encode_sample(0) == 0xFF
    assert mulaw_decode_sample(0xFF) == 0 and mulaw_decode_sample(0x7F) == 0
    assert mulaw_decode_sample(0x00) == -32124 and mulaw_decode_sample(0x80) == 32124
    # every code decodes then re-encodes to an equivalent code (0x7F and 0xFF are both zero)
    for b in range(256):
        again = mulaw_encode_sample(mulaw_decode_sample(b))
        assert mulaw_decode_sample(again) == mulaw_decode_sample(b), b
    # round trip error stays within G.711 quantisation step for a 440 Hz tone
    tone = array.array("h", (int(12000 * math.sin(2 * math.pi * 440 * t / 8000)) for t in range(800)))
    back = array.array("h")
    back.frombytes(mulaw_decode(mulaw_encode(tone.tobytes())))
    worst = max(abs(a - b) for a, b in zip(tone, back))
    assert worst <= 512, worst
    assert mulaw_encode_sample(40000) == mulaw_encode_sample(32767)  # clipped
    up = resample(tone.tobytes(), 8000, 16000)
    assert len(up) == 2 * len(tone.tobytes())
    assert len(resample(up, 16000, 8000)) == len(tone.tobytes())
    assert frame_bytes(8000, 20, "mulaw") == 160 and frame_bytes(16000, 20, "pcm16") == 640
    assert frame_bytes(24000, 20, "pcm16") == 960
    stereo = array.array("h", [100, 300, -50, -150]).tobytes()
    assert array.array("h", to_mono(stereo, 2)).tolist() == [200, -100]
    assert array.array("h", to_mono(array.array("h", [1, 2, 3]).tobytes(), 2)).tolist() == [1]
    # anti-aliasing: a 6 kHz tone at 24 kHz must be strongly attenuated at 8 kHz (Nyquist 4 kHz)
    hi = array.array("h", (int(12000 * math.sin(2 * math.pi * 6000 * t / 24000)) for t in range(2400)))
    down = array.array("h")
    down.frombytes(resample(hi.tobytes(), 24000, 8000))
    rms = math.sqrt(sum(x * x for x in down[50:-50]) / len(down[50:-50]))
    assert rms < 12000 / math.sqrt(2) * 0.1, rms   # >20 dB down
    # a 1 kHz tone passes almost unchanged
    lo = array.array("h", (int(12000 * math.sin(2 * math.pi * 1000 * t / 24000)) for t in range(2400)))
    down = array.array("h")
    down.frombytes(resample(lo.tobytes(), 24000, 8000))
    rms = math.sqrt(sum(x * x for x in down[50:-50]) / len(down[50:-50]))
    assert rms > 12000 / math.sqrt(2) * 0.9, rms
    assert resample(b"", 8000, 16000) == b"" and len(resample(b"\x01\x00", 8000, 16000)) == 4
    print("voice_audio self-test passed")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Telephony audio toolkit (mu-law, resampling, frames)")
    ap.add_argument("--self-test", action="store_true")
    sub = ap.add_subparsers(dest="cmd")
    i = sub.add_parser("info", help="Show a WAV file's format and duration")
    i.add_argument("wav")
    t = sub.add_parser("to-mulaw", help="16-bit WAV -> raw 8 kHz mono mu-law (what Twilio streams)")
    t.add_argument("wav")
    t.add_argument("out")
    f = sub.add_parser("from-mulaw", help="Raw 8 kHz mu-law -> 16-bit WAV")
    f.add_argument("ulaw")
    f.add_argument("out")
    f.add_argument("--rate", type=int, default=8000, help="Output sample rate (resampled from 8 kHz)")
    fr = sub.add_parser("frames", help="Frame size maths")
    fr.add_argument("--rate", type=int, default=8000)
    fr.add_argument("--ms", type=int, default=20)
    fr.add_argument("--codec", choices=["mulaw", "alaw", "pcm16"], default="mulaw")
    a = ap.parse_args(argv)
    if a.self_test:
        _self_test()
        return 0
    try:
        if a.cmd == "info":
            pcm, rate, ch = read_wav(a.wav)
            secs = len(pcm) / (2 * ch * rate)
            print(f"{rate} Hz, {ch} channel(s), 16-bit PCM, {secs:.2f} s")
            if rate != 8000 or ch != 1:
                print("for telephony streams convert to 8 kHz mono mu-law: to-mulaw")
        elif a.cmd == "to-mulaw":
            pcm, rate, ch = read_wav(a.wav)
            data = mulaw_encode(resample(to_mono(pcm, ch), rate, 8000))
            with open(a.out, "wb") as fh:
                fh.write(data)
            print(f"wrote {len(data)} bytes ({len(data) / 8000:.2f} s of 8 kHz mu-law)")
        elif a.cmd == "from-mulaw":
            with open(a.ulaw, "rb") as fh:
                pcm = mulaw_decode(fh.read())
            write_wav(a.out, resample(pcm, 8000, a.rate), a.rate)
            print(f"wrote {a.out} at {a.rate} Hz")
        elif a.cmd == "frames":
            n = frame_bytes(a.rate, a.ms, a.codec)
            print(f"{a.ms} ms of {a.rate} Hz {a.codec} = {n} bytes "
                  f"({n * 4 // 3 + (4 - n * 4 // 3 % 4) % 4} chars base64)")
        else:
            ap.print_help()
            return 2
    except (OSError, ValueError, wave.Error, EOFError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
