---
name: calling-compliance
description: Engineering checklist for AI voice agents that make or answer phone calls - US TCPA (AI voices are "artificial voice" under FCC 24-17, prior express written consent, 8am-9pm calling hours, DNC lists, identification and opt-out, the November 2026 consent-revocation rules, STIR/SHAKEN), state recording-consent and AI-disclosure laws, India TRAI rules (DLT, 140 and 1600 series, the 2026 amendment treating AI calls as A2P), EU AI Act Article 50 disclosure, GDPR and UK PECR, PCI DSS for card numbers on calls, and voiceprint biometrics. Use when building outbound calling, appointment reminders, sales or collections agents, call recording, or reviewing a voice product before launch. Engineering guidance, not legal advice.
---

# Calling compliance for AI voice agents

Phone rules carry per-call damages, so one bad campaign can cost more than the
product. Build compliance into the dialer and the agent, not into a policy
document. Facts checked in **November 2026** against FCC, TRAI, EU and UK
sources and law-firm summaries. Laws are changing fast here: confirm with
counsel for your markets before launch.

## United States (TCPA, 47 CFR 64.1200)

- **AI voices are "artificial or prerecorded voice"** (FCC Declaratory Ruling
  FCC 24-17, February 2024). Every robocall rule applies to AI voice agents.
- **Consent:** prior express consent for informational calls to mobiles;
  **prior express written consent** (signed, e-signature ok, identifying the
  number, stating consent is not a condition of purchase) for telemarketing.
  The 2023 "one-to-one consent" rule was vacated (11th Circuit, January 2025).
- **Hours:** telephone solicitations only **8 am - 9 pm in the called party's
  local time** (64.1200(c)(1)). Derive timezone from the number and address;
  when unsure, use the narrowest window.
- **Do-not-call:** scrub against the National DNC Registry and your internal
  list; honour internal DNC requests within a reasonable time, at most 10
  business days.
- **At the start of every artificial-voice call** (64.1200(b)): state the
  business responsible and a callback number that accepts DNC requests. For
  telemarketing, offer an automated **voice or key-press opt-out within 2
  seconds** of that identification; opting out must record the number and end
  the call. Voicemails need a toll-free callback number.
- **Revocation:** consent can be revoked by any reasonable means and must be
  honoured within **10 business days** (for text messages, replies like "stop",
  "unsubscribe", "opt out", "cancel" revoke conclusively; on voice calls the
  required mechanism is the automated voice or key-press opt-out). FCC Report and Order FCC 26-67
  (effective around **25 November 2026**) lets callers designate an exclusive
  revocation method if clearly disclosed and lets revocations be limited to the
  category of calls they target; a further proposal would shorten 10 to 7
  business days. Your agent should treat any opt-out phrase as a revocation.
- **Caller ID:** calls must be signed under STIR/SHAKEN; confirm your carrier or
  CPaaS signs with A-level attestation using its own certificate (FCC 24-120,
  effective 18 September 2025). Never spoof numbers.
- **Damages:** $500 per call, up to $1,500 if wilful (47 USC 227(b)(3)).
- FCC rules requiring AI-specific disclosure are proposed (FCC 24-84), not final.

## US states

- **All-party consent to record** phone calls: California, Delaware, Florida,
  Illinois, Maryland, Massachusetts, Montana, Nevada, New Hampshire,
  Pennsylvania, Washington (Connecticut also commonly listed; Michigan
  disputed). Across states, the strictest rule applies - **announce recording on
  every call**.
- **Mini-TCPAs** (Florida FTSA, Oklahoma) add their own consent and hour rules.
- **AI/bot disclosure:** California SB 1001 (bots selling or influencing votes),
  Utah's AI Policy Act (disclose when asked; up front in regulated
  occupations), and a wave of 2025-2026 chatbot laws (New York, New Jersey,
  Maine, Washington from 1 January 2027). Simplest compliant design: disclose
  that the caller is an AI at the start of every call.

## India (TRAI TCCCPR 2018 and amendments)

- Register as a principal entity on the operator **DLT** platform with headers
  and templates.
- **140-series** numbers for promotional calls; **1600-series** for service and
  transactional calls. Banks, NBFCs, insurers, mutual funds and brokers had to
  move to 1600 numbers between 1 January and 15 March 2026; after that, other
  numbers are not allowed for those calls.
- **Third Amendment 2026** (notified 18 September 2026): autodialled,
  prerecorded and **AI-voice calls are A2P** and must be declared in advance,
  with their number ranges, to the originating operator; undeclared automated
  calls count as spam. Operators use AI spam detection; 5+ flagged numbers in 10
  days can trigger restriction or disconnection; telemarketers can be
  blacklisted for a year; consent and inquiry records must be verifiable.
- Respect DND preferences; keep verifiable consent and inquiry records.
- No specific call-recording statute; announce recording and limit its use.
  Recordings and transcripts are personal data under the DPDP Act (main duties
  from about May 2027).

## EU and UK

- **EU AI Act Article 50:** from **2 August 2026** people must be told they are
  interacting with an AI system unless obvious. (The 2026 Digital Omnibus moved
  only the separate machine-readable marking duty for synthetic content.)
- **GDPR:** a lawful basis for recording and transcription, a notice at the start
  of the call, and explicit consent for voiceprints used to identify people.
- **UK PECR regulation 19:** prior consent specifically for **automated
  marketing calls**; fines since February 2026 can reach £17.5m or 4% of
  turnover. Ofcom treats silent and abandoned calls as persistent misuse.

## Card numbers and biometrics

- **Never let spoken card numbers reach STT, the LLM, logs or recordings.**
  Hand off to DTMF capture with masking, or a secure IVR / payment link (PCI SSC
  telephone payments guidance). Pausing recordings manually is error-prone.
- **Voiceprints:** Illinois BIPA requires written notice and release before
  collecting them ($1,000-$5,000 damages); GDPR treats them as special-category data.
- **Voice cloning:** only clone voices with documented consent; impersonation and
  election deepfake calls have drawn multi-million-dollar FCC fines.

## Build checklist

- [ ] Consent store: who, what number, which call types, when, how, and the text shown; checked before every dial.
- [ ] Dialer enforces local-time windows, DNC scrubbing and per-number frequency caps.
- [ ] Call opening script: AI disclosure, business name, callback number, recording notice, opt-out instructions (2-second rule for telemarketing).
- [ ] The agent recognises opt-out phrases at any point, confirms, records the revocation and ends the call.
- [ ] Caller ID is a number you own, signed with A-level STIR/SHAKEN attestation.
- [ ] India: DLT registration, 140/1600 series, automated-call declaration to the operator.
- [ ] Card payments routed to DTMF masking or a payment link; transcripts and recordings redacted.
- [ ] Recordings and transcripts: retention limits, access control, deletion on request.
- [ ] Audit log of every call attempt, consent check and opt-out.
