# Changelog

All notable changes are listed here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-11-23

### Added
- `voice-agents` Claude Code plugin with 7 skills: `voice-agent-architecture`,
  `telephony-integration`, `voice-prompting`, `latency-tuning`,
  `voice-agent-testing`, `calling-compliance`, `audio-formats`.
- `voice_audio.py`: G.711 mu-law encode/decode (no `audioop`, works on Python
  3.13+), resampling, mono conversion, WAV conversion and frame-size maths.
- `latency_report.py`: per-stage p50/p90/p95 and voice-to-voice latency from
  JSONL events or CSV, with slow-turn and clock-skew detection.
- Facts checked against Twilio, Plivo, Exotel, OpenAI, Google, Pipecat,
  LiveKit, FCC, TRAI, EU and UK sources in November 2026.
