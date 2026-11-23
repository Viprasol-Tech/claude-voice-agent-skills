---
name: voice-agent-architecture
description: Choose and design the architecture of an AI voice agent - cascaded STT to LLM to TTS pipelines vs. speech-to-speech realtime models (OpenAI Realtime, Gemini Live), frameworks (Pipecat, LiveKit Agents) vs. hosted platforms, telephony entry points (WebSocket media streams vs. SIP), turn detection and endpointing, barge-in, tool calling, state and handoff to humans, hosting regions and concurrency. Use when starting a voice agent project, picking vendors or frameworks, migrating between them, or reviewing a voice agent design for latency, cost and reliability.
---

# Voice agent architecture

Every design is a trade-off between latency, control, cost and how much you
have to build. Decide the big pieces in this order: **how audio arrives, how
speech becomes a response, how turns are managed, and where it runs.** Vendor
and model facts below were checked in **November 2026**; they change quickly.

## 1. Pipeline shape

| | Cascaded (STT -> LLM -> TTS) | Speech-to-speech (realtime model) |
|---|---|---|
| Latency | Sum of three stages; well-tuned ~0.8-1.4 s voice-to-voice | Often lowest; one model, no handoffs |
| Control | Pick each vendor; inspect text at every step; easy guardrails | Less visibility; prompt and tools only |
| Voices and languages | Any TTS voice, any STT language (strong for Indian languages) | Limited to the model's voices and languages |
| Cost | Pay per component; can mix cheap and premium | Usually priced per audio token |
| Best for | Regulated flows, custom voices, Indic languages, strict scripts | Open conversation, fastest feel |

Speech-to-speech options as of November 2026: **OpenAI Realtime**
(`gpt-realtime-2.1` and `-mini`; WebRTC, WebSocket or SIP; accepts `audio/pcm`
at 24 kHz and G.711 `audio/pcmu`/`audio/pcma`, so telephony μ-law can pass
through), and **Gemini Live** (WebSocket; 16 kHz PCM in, 24 kHz out; audio
sessions 15 minutes unless context compression is enabled, connections about 10
minutes with a `GoAway` warning). Check current model names before coding.

## 2. Build, framework or platform

- **Framework** (open source): **Pipecat** (pipeline of frame processors, Twilio
  and Exotel serializers, Smart Turn endpointing) or **LiveKit Agents**
  (`AgentSession` + `Agent`, turn-detector model, built-in SIP with tested
  trunks including Twilio, Telnyx, Exotel and Plivo). Most control per effort.
- **Hosted platforms** (Vapi, Retell, ElevenLabs Agents, Twilio ConversationRelay
  and similar): fastest to launch, less control, per-minute pricing, vendor lock-in.
- **Fully custom**: only if you need something frameworks cannot do; you will
  rebuild interruption handling, endpointing and transport.

## 3. How audio arrives

- **Media streams over WebSocket** (Twilio `<Connect><Stream>`, Plivo
  bidirectional stream, Exotel Voicebot applet): your server receives and sends
  base64 audio frames. Simple, works with any pipeline. See `telephony-integration`.
- **SIP** (LiveKit SIP, OpenAI Realtime SIP, a SIP trunk to your media server):
  better call control (transfers via REFER, DTMF), fewer hops at scale.
- **WebRTC** for browser and app voice: lowest latency over the internet, built
  into LiveKit and the realtime APIs.

## 4. Turns and interruptions

- **Endpointing** (deciding the caller finished) dominates perceived latency.
  Fixed silence timers (~500-800 ms) feel slow and still cut people off;
  **semantic/model-based** turn detection (Pipecat Smart Turn, LiveKit
  turn-detector, OpenAI `semantic_vad`) typically decides in ~200-400 ms.
- **Barge-in:** when the caller speaks, stop TTS immediately, flush buffered
  audio (Twilio `clear`, Plivo `clearAudio`, Exotel `clear`), cancel the LLM
  response, and truncate the conversation history to what was actually heard.
- Ignore short backchannels ("mm-hmm") as interruptions where the framework allows.

## 5. Tools, state and handoff

- Tools for every action and lookup; confirm before state changes; idempotent
  server-side (see `voice-prompting`).
- Keep call state (caller id, verified identity, collected fields) outside the
  LLM context, and pass only what the model needs.
- Human handoff: warm or cold transfer (SIP REFER or provider transfer API), with
  a summary passed to the agent.
- Payments: hand off to DTMF/secure IVR or send a payment link; never take card
  numbers through STT (see `calling-compliance`).

## 6. Where it runs

- Co-locate the agent server, STT, LLM and TTS endpoints in one region near the
  telephony media edge (for India, use Indian regions where vendors offer them;
  also needed for data residency).
- Keep provider WebSockets and HTTP connections warm.
- Plan concurrency: each call holds a WebSocket and several streaming
  connections; load-test against provider rate limits.

## Decision checklist

- [ ] Pipeline shape chosen for the languages, voices, control and latency required.
- [ ] Framework / platform chosen; exit cost understood.
- [ ] Telephony path chosen (media stream vs. SIP) and audio format matched end to end (`audio-formats`).
- [ ] Model-based endpointing and full barge-in handling (flush, cancel, truncate).
- [ ] Tools idempotent; human handoff and payment handoff designed.
- [ ] Region and data residency decided; per-stage latency budget set (`latency-tuning`).
- [ ] Test plan in place (`voice-agent-testing`); compliance reviewed (`calling-compliance`).
