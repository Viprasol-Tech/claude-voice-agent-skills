---
name: telephony-integration
description: Connect AI voice agents to phone calls through Twilio Media Streams (bidirectional Connect Stream, media, mark, clear, dtmf events, 8 kHz mu-law), Plivo audio streaming (playAudio, checkpoint, clearAudio), Exotel Voicebot and Stream applets (16-bit PCM, chunk rules) and SIP trunks - with correct barge-in handling, call control, DTMF, transfers, security and Indian telephony options. Use when wiring a voice agent to a phone number, writing a media-stream WebSocket server, debugging choppy, silent or one-way audio, or moving between telephony providers.
---

# Telephony integration

Most "the bot can't hear me" or "the audio is choppy" bugs are format or
framing mismatches. Match the provider's codec, sample rate and frame rules
exactly, and use its playback markers to know what the caller actually heard.
Protocol facts checked against provider docs in **November 2026**.

## Twilio Media Streams

Docs: <https://www.twilio.com/docs/voice/media-streams/websocket-messages>

- Use **`<Connect><Stream url="wss://...">`** for a bidirectional agent (one per
  call). It blocks later TwiML until your server closes the socket.
  `<Start><Stream>` only forks audio one way and cannot send audio back.
- `url` must be `wss://` with no query string; pass data with nested
  `<Parameter name value>` (arrives in `start.customParameters`).
- **Inbound messages:** `connected`, `start` (`streamSid`, `callSid`,
  `mediaFormat`), `media` (`payload` base64, `timestamp`, `chunk`), `mark`,
  `dtmf`, `stop`. Audio is **`audio/x-mulaw`, 8000 Hz, mono**.
- **Send audio:** `{"event":"media","streamSid":"...","media":{"payload":"<base64 raw mu-law>"}}`
  - raw bytes only, no WAV header. Twilio queues and plays in order.
- **Know what was heard:** after sending audio, send
  `{"event":"mark","streamSid":"...","mark":{"name":"turn-7"}}`; Twilio echoes it
  when playback reaches it.
- **Barge-in:** send `{"event":"clear","streamSid":"..."}` to drop queued audio;
  Twilio returns pending marks so you know what was never played.
- Validate `X-Twilio-Signature` on webhooks; restrict the WebSocket endpoint.

## Plivo

Docs: <https://www.plivo.com/docs/voice/audio-streaming/overview>

- `<Stream bidirectional="true" keepCallAlive="true" contentType="audio/x-mulaw;rate=8000">`
  (or `audio/x-l16;rate=16000`); `extraHeaders` are echoed back on events.
- Inbound: `start`, `media` (about 20 ms chunks), `dtmf`, `playedStream`, `clearedAudio`.
- Outbound: `playAudio` (format must match the stream), `checkpoint` (Plivo
  replies `playedStream` when reached), `clearAudio`, `sendDTMF`.

## Exotel (India)

Docs: <https://developer.exotel.com/docs/agentstream/stream-voicebot-applet>

- **Voicebot applet** is bidirectional; the Stream applet is one-way.
- Audio is raw 16-bit little-endian mono PCM, base64. Select the rate with
  `?sample-rate=8000|16000|24000` on the WSS URL and **confirm it from
  `start.media_format`** (documentation differs on the default).
- Events use snake_case (`stream_sid`, `call_sid`): `connected`, `start`,
  `media`, `dtmf`, `mark`, `stop` (reason `stopped` or `callended`); you send
  `media`, `mark`, `clear`.
- Outbound chunks: at least 3.2 KB, at most 100 KB, **a multiple of 320 bytes**,
  or audio gaps appear; smaller chunks make `clear` react faster.
- Auth by IP allow-list or Basic Auth in the WSS URL; up to 3 custom parameters.

Other Indian options: Plivo (above); Vobiz and Ozonetel are reported to
support bidirectional streaming via partner integrations; LiveKit SIP has been
tested with Exotel and Plivo. Indian outbound calling also needs TRAI DLT
registration and the right number series (see `calling-compliance`).

## SIP

- Use SIP (LiveKit SIP, OpenAI Realtime SIP, your own SBC) for call control at
  scale: transfers via REFER, DTMF via RFC 2833/4733, fewer media hops.
- Make sure caller ID is signed (STIR/SHAKEN in the US) and codecs are
  negotiated as expected (G.711 μ-law/A-law for PSTN).

## Server loop (media streams)

```text
on start: read stream id + format; open STT/LLM/TTS (or realtime) sessions
on media: decode base64 -> (mu-law -> PCM16 if needed) -> resample -> send to STT/VAD
on agent audio: resample -> (PCM16 -> mu-law if needed) -> frame -> base64 -> send media
             -> send mark after each utterance
on caller speech start (barge-in): send clear; cancel LLM/TTS; truncate history to last mark
on dtmf: route to the agent as a tool input (for example menu choice, PIN via secure flow)
on stop / socket close: close vendor sessions; write call summary and logs
```

Use `audio-formats` for conversion and frame sizes.

## Troubleshooting

| Symptom | Usual cause |
|---|---|
| Robotic or chipmunk audio | Wrong sample rate (16 kHz audio sent as 8 kHz, or vice versa) |
| Static / white noise | PCM sent where mu-law expected (or a WAV header in the payload) |
| Agent talks over the caller | No `clear` on barge-in; TTS keeps streaming |
| Agent repeats or loses context after interruption | History not truncated to what was played (no marks) |
| Gaps in Exotel audio | Chunks not a multiple of 320 bytes or below the minimum size |
| Call ends when the stream closes | Expected for `<Connect><Stream>`; return new TwiML to transfer instead |

## Review checklist

- [ ] Codec, sample rate and channels match the provider exactly in both directions.
- [ ] Marks/checkpoints used to track playback; clear on barge-in; history truncated.
- [ ] Webhook signatures verified; WebSocket endpoints authenticated or IP-restricted.
- [ ] DTMF handled; transfers implemented with the provider's call-control API.
- [ ] Reconnect and timeout handling; vendor sessions closed on `stop`.
- [ ] Caller ID owned and signed; Indian calling registered with DLT.
