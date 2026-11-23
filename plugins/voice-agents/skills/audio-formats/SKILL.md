---
name: audio-formats
description: Handle telephony and voice AI audio formats correctly - G.711 mu-law and A-law vs. 16-bit PCM, 8 / 16 / 24 kHz sample rates used by phone networks, STT, TTS and realtime models, resampling, mono conversion, frame sizes (20 ms = 160 bytes of 8 kHz mu-law), base64 framing for media streams, WAV headers, and replacing Python's removed audioop module. Includes a tested converter. Use when audio sounds distorted, robotic, noisy or silent between a phone provider and an AI model, when writing conversion code, or when sizing audio chunks.
allowed-tools: Bash(python ${CLAUDE_SKILL_DIR}/scripts/voice_audio.py *)
---

# Audio formats for voice agents

Every hop in a voice agent can expect a different format. The phone network
speaks 8 kHz G.711; speech recognisers prefer 16 kHz PCM; TTS and realtime
models often emit 24 kHz PCM. Convert deliberately at the edges, once each way.

## Formats you will meet

| Where | Typical format |
|---|---|
| Twilio Media Streams | G.711 **mu-law**, 8000 Hz, mono, base64 |
| Plivo streams | mu-law 8 kHz or L16 (PCM16) 8/16 kHz, as configured |
| Exotel Voicebot | PCM16 little-endian mono, 8/16/24 kHz (check `start.media_format`) |
| Most STT APIs | PCM16 16 kHz mono (many also accept mu-law 8 kHz directly) |
| TTS APIs | PCM16 at 16-48 kHz, or mu-law 8 kHz if you request it |
| OpenAI Realtime | `audio/pcm` 24 kHz, or G.711 `audio/pcmu` / `audio/pcma` |
| Gemini Live | PCM16 16 kHz in, 24 kHz out |

Ask STT/TTS vendors for the telephony format directly when they support it
(for example mu-law 8 kHz output from TTS); every conversion you skip saves
latency and quality.

## Frame sizes

```text
bytes per frame = sample_rate x frame_ms / 1000 x bytes_per_sample
20 ms of 8 kHz mu-law   = 160 bytes  (216 base64 characters)
20 ms of 8 kHz PCM16    = 320 bytes
20 ms of 16 kHz PCM16   = 640 bytes
20 ms of 24 kHz PCM16   = 960 bytes
```

Some providers add their own rules (Exotel: outbound chunks of at least 3.2 KB,
in multiples of 320 bytes).

## Converter

Python 3.13 removed `audioop` (PEP 594), which many tutorials still use for
mu-law. The bundled script implements G.711 mu-law with the standard library
(or install `audioop-lts` on 3.13+ if you prefer the old API).

```bash
A=${CLAUDE_SKILL_DIR}/scripts/voice_audio.py
python $A info recording.wav
python $A to-mulaw prompt.wav prompt.ulaw            # -> 8 kHz mono mu-law for Twilio
python $A from-mulaw caller.ulaw caller.wav --rate 16000
python $A frames --rate 16000 --ms 20 --codec pcm16
python $A --self-test
```

In code, import `mulaw_encode`, `mulaw_decode` and `frame_bytes` freely - the
mu-law codec is stateless, so it is safe on 20 ms chunks. `resample` (low-pass
filter + interpolation) is for **whole buffers** such as prompts and files; it
does not carry filter state or phase between calls, so resampling a live stream
chunk by chunk with it causes clicks. For live streams use **soxr**,
**libsamplerate**, or `audioop-lts` `ratecv` with its state - or ask the TTS
vendor for 8 kHz mu-law output and skip resampling entirely.

## Rules

- PCM16 is **little-endian** on the wire for these providers; never send a WAV
  header inside a media payload.
- Keep mono; phone audio is mono.
- Do not resample twice (8 -> 16 -> 8); plan the chain once.
- Apply noise suppression on the inbound side before STT if the vendor does not.
- Put silence or comfort noise in gaps only if the provider requires a continuous stream.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| Fast, high-pitched ("chipmunk") | Audio played at a higher rate than it was recorded |
| Slow, deep | Played at a lower rate than recorded |
| Loud static | PCM bytes sent as mu-law, or a WAV header in the payload |
| Crackles at chunk joins | Odd byte counts for PCM16, or uneven chunk sizes |
| Silence | Wrong base64, wrong stream id, or audio sent before the stream started |
