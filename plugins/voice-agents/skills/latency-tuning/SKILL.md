---
name: latency-tuning
description: Measure and reduce AI voice agent latency - voice-to-voice and per-stage budgets (endpointing, STT final, LLM time to first token, TTS time to first audio, transport), p50 and p95 from real call logs, endpointing and turn-detection tuning, streaming everywhere, prompt and model choices, co-location and warm connections, filler speech for slow tools, and tail-latency spikes. Includes a tested per-stage latency report script. Use when a voice agent feels slow, when comparing vendors or models, setting latency targets, or instrumenting a voice pipeline.
allowed-tools: Bash(python ${CLAUDE_SKILL_DIR}/scripts/latency_report.py *)
---

# Latency tuning

Callers judge an agent by the gap between when they stop talking and when it
starts. Measure that gap per stage on **real calls**, fix the biggest stage
first, and watch p95 - the slow turns are what people remember.

## Targets

Twilio's published guidance (November 2025) for cascaded agents, as medians:

| Stage | Target | Upper bound |
|---|---|---|
| STT (to final transcript) | 350 ms | 500 ms |
| LLM time to first token | 375 ms | 750 ms |
| TTS time to first byte | 100 ms | 250 ms |
| Platform turn gap | 885 ms | 1,100 ms |
| Mouth-to-ear turn gap | 1,115 ms | 1,400 ms |

"About 800 ms voice-to-voice" is a common industry target, not a standard.
Independent measurements often find medians well above 1 s with p95 above 2 s,
so set targets from your own baseline.

## Measure

Log a timestamp per turn for each stage and run the report:

```text
user_speech_end -> stt_final -> llm_first_token -> tts_first_audio -> agent_audio_start
```

```bash
python ${CLAUDE_SKILL_DIR}/scripts/latency_report.py events.jsonl --slow 1500
python ${CLAUDE_SKILL_DIR}/scripts/latency_report.py turns.csv --unit ms --json
```

Events are JSON lines like `{"call": "c1", "turn": 3, "event": "stt_final", "t": 12.345}`
(seconds, or `--unit ms`), or a CSV with one row per turn and a column per
stage. The report prints p50/p90/p95 per stage and voice-to-voice, lists the
slowest turns, and warns about out-of-order timestamps (clock skew between
services - use one clock, or monotonic time on one machine).

## Fix in this order

1. **Endpointing.** Fixed silence timeouts (~500-800 ms) are often the largest
   single delay. Use model-based turn detection (Pipecat Smart Turn, LiveKit
   turn-detector, OpenAI `semantic_vad`), which typically decides in ~200-400 ms,
   with a silence fallback. Watch for tail spikes when the model is unsure.
2. **LLM time to first token.** Smaller or faster models for conversational
   turns; shorter system prompts and trimmed history; avoid reasoning modes on
   every turn; stream tokens; keep tool calls off the critical path or speak a
   short filler while they run.
3. **TTS time to first audio.** Streaming TTS fed with the first sentence (or
   clause) as soon as it arrives; reuse connections; pick low-latency voices.
4. **Transport.** Co-locate the agent, STT, LLM and TTS near the telephony media
   region; keep WebSockets warm; avoid needless resampling and transcoding (pass
   G.711 through when the model accepts it); small output chunks.
5. **Speech-to-speech models** remove two handoffs; consider them when the
   cascaded pipeline cannot get under target.

## Perceived latency tricks

- Start speaking with a short, natural acknowledgement while the full answer is
  generated ("Sure - ").
- For slow lookups, say what you are doing ("Let me check your booking").
- Never leave more than ~2 s of silence without a sound or a word.

## Review checklist

- [ ] Every turn logs stage timestamps from one clock; dashboards show p50/p95 per stage.
- [ ] Model-based endpointing with a silence fallback; thresholds tuned on real calls.
- [ ] LLM, TTS and STT all streaming; TTS starts on the first sentence.
- [ ] Prompt and history trimmed; fast model for conversation, slower ones only when needed.
- [ ] Services co-located with the media region; connections kept warm.
- [ ] Filler speech for slow tools; no long silences.
- [ ] Latency regression checks run on every change (`voice-agent-testing`).
