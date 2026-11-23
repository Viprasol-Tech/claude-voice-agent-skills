---
name: voice-agent-testing
description: Test and evaluate AI voice agents before and after launch - scenario suites with simulated callers, scripted test calls over real phone lines, transcript and audio review, task-success and tool-call accuracy, latency and interruption tests, ASR word error rate on your own audio, regression checks when prompts or models change, load tests for concurrent calls, and production monitoring with alerts. Use when preparing a voice agent for production, comparing STT/LLM/TTS vendors, investigating bad calls, or setting up CI and dashboards for a voice product.
---

# Testing voice agents

A voice agent can pass every text test and still fail on the phone: background
noise, accents, interruptions, line quality and latency only show up in audio.
Test in layers, from cheap and fast to real calls.

## Layers

| Layer | What it catches | How |
|---|---|---|
| 1. Text conversation tests | Prompt logic, tool use, policy breaks | Run the agent's LLM loop on scripted user turns; assert on tool calls and replies |
| 2. Simulated callers | Multi-turn behaviour, edge cases | A second LLM plays a caller persona (impatient, confused, off-topic, non-native speaker, tries to get a refund) against the agent, text or TTS-to-STT |
| 3. Audio pipeline tests | STT errors, TTS pronunciation, barge-in, endpointing | Feed recorded or synthesised audio through the real pipeline; check transcripts and timing |
| 4. Real test calls | Telephony, codec, network, carrier issues | Scripted calls over real numbers, ideally from different carriers and regions |
| 5. Production monitoring | Drift, outages, new failure patterns | Sample calls for review, dashboards, alerts |

## What to measure

- **Task success:** did the call achieve its goal (booking made, lead
  qualified, issue resolved)? Define it per scenario, judged from the
  transcript and the tool calls.
- **Tool accuracy:** right tool, right arguments, confirmed before acting, no
  duplicate actions.
- **Policy compliance:** disclosures said, opt-outs honoured, no card numbers
  collected by voice, no invented prices (see `calling-compliance`).
- **Latency:** voice-to-voice p50/p95 per turn and per stage
  (`latency-tuning` has a report script).
- **Interruptions:** does the agent stop speaking within a few hundred
  milliseconds and answer the new input?
- **ASR quality:** word error rate on **your** callers' audio, and especially
  entity accuracy (names, numbers, addresses) - general WER benchmarks hide
  this.
- **Experience:** call length, transfers to humans, hang-ups mid-call, repeat
  callers.

## Scenario suite

Write scenarios as data so they run in CI:

```yaml
- name: reschedule_with_interruption
  persona: "busy parent, interrupts often, wants Thursday after 5 pm"
  goal: "appointment moved to an available Thursday slot after 5 pm"
  must_call: [check_availability, reschedule_appointment]
  must_not: ["collects card number", "books without confirming"]
  max_turns: 12
- name: opt_out_midway
  persona: "says 'stop calling me' after the greeting"
  goal: "agent confirms, records opt-out, ends call"
  must_call: [record_opt_out, end_call]
```

Grade with a mix of deterministic checks (tool calls, phrases) and an LLM judge
with a written rubric; spot-check the judge against human ratings.

## Regression and release

- Re-run the full suite on every prompt, model, voice or vendor change.
- Keep a set of real (consented, redacted) failed calls as permanent tests.
- Roll out changes to a small share of traffic first and compare task success,
  latency and hang-up rate before going to 100%.
- Load-test concurrency: many simultaneous calls expose rate limits on STT, LLM
  and TTS providers and on your WebSocket servers.

## Production monitoring

- Log per turn: timestamps for each stage, transcript, tool calls, errors, and a
  call outcome label. Redact card numbers and sensitive identifiers before storage.
- Alert on: p95 latency jumps, error rates per provider, spikes in transfers or
  short calls, and opt-out failures.
- Review a random sample of calls every week, plus every escalation.

## Review checklist

- [ ] Scenario suite covers happy paths, interruptions, silence, opt-outs, angry and confused callers, and each language served.
- [ ] Assertions on tool calls and compliance phrases, not just "looks fine".
- [ ] Real test calls over the production telephony path before launch.
- [ ] Latency measured per stage on real calls.
- [ ] Regression suite runs on every prompt/model/vendor change.
- [ ] Production dashboards and alerts in place; calls sampled for human review.
