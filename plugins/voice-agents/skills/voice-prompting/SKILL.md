---
name: voice-prompting
description: Write system prompts and tool designs for AI voice agents that sound natural on a phone call - short spoken sentences, no markdown or lists, numbers, dates, currency and emails written to be spoken, confirming names and digits, one question at a time, handling interruptions, silence and off-topic callers, safe tool calling for bookings and payments, escalation to a human, and multilingual or code-switched calls such as Hindi-English (Hinglish). Use when writing or reviewing a voice agent's prompt, persona, call script or function definitions, or when an agent sounds robotic, talks too long or mishears details.
---

# Prompting voice agents

Text prompts fail on the phone. Users cannot scroll back, skim a list or see a
link, and every extra second of speech costs attention and latency. Write the
prompt for the ear.

## Prompt skeleton

```text
You are <name>, a voice assistant for <business>, speaking with a caller on the phone.
Goal: <one sentence: what a successful call achieves>.

How to speak
- Reply in one or two short sentences. Ask only one question at a time.
- Plain spoken language. No lists, markdown, emojis, URLs or symbols.
- Say numbers the way people say them: "two thirty pm", "rupees four hundred and ninety nine".
- Read back phone numbers, amounts, dates and spellings to confirm before acting.
- If you did not catch something, say so and ask again; never guess.
- If interrupted, stop and answer what the caller just said.

What you can do
- <tool>: when to use it, what to confirm first.
- Hand off to a human when: <caller asks>, <you fail twice>, <angry or vulnerable caller>, <payment>.

What you must not do
- Do not invent prices, policies or availability; use the tools.
- Do not collect card numbers or passwords by voice.
- <compliance items: AI disclosure, recording notice, opt-out handling - see calling-compliance>

Opening line: "<exact first sentence, including AI and recording disclosure where required>"
```

Keep the prompt short and specific. Long prompts raise time-to-first-token on
every turn (see `latency-tuning`).

## Speaking rules that matter

| Problem | Rule |
|---|---|
| Rambling answers | Hard cap: 1-2 sentences, ~25 words; offer more only if asked |
| Lists read aloud | Offer two or three options in a sentence, or ask a narrowing question |
| Digits misheard | Group digits ("nine eight seven, six five four...") and confirm by reading back |
| Emails and spellings | Spell with "A for apple" style confirmation; prefer sending a link by SMS |
| Dates and times | Always say the day and the time zone the caller expects ("Tuesday the 4th, 3 pm your time") |
| Currency | Spoken form with currency word, never symbols |
| Silence | After ~5-7 s, a short check-in ("Are you still there?"); end politely after a second silence |
| Interruptions | The transport stops TTS on barge-in; the prompt tells the model to drop its previous point |

Many TTS engines also support SSML or pronunciation dictionaries for brand
names, abbreviations and Indian names; use them rather than misspelling words
in the prompt.

## Tools (function calling)

- One tool per action (`check_availability`, `book_appointment`,
  `transfer_to_human`, `end_call`), with tight parameter types.
- Confirm details aloud **before** any tool that changes something; the tool
  should still validate server-side.
- Make actions idempotent (a booking id per call and slot) so a retried tool
  call does not double-book.
- Say a short filler while a slow tool runs ("Let me check that for you").
- Never put secrets, full card numbers or internal IDs into what the model may say.

## Multilingual and Hinglish calls

- Choose STT and TTS that support the target languages and **code-switching**;
  Hindi-English mixing within one sentence is normal in India.
- Tell the model to reply in the caller's language and mix, and to keep
  entity values (names, amounts, dates) unambiguous - repeat digits in English
  if that is what the caller used.
- Use the right script for TTS input (Devanagari for Hindi voices) and test
  pronunciation of numbers and rupee amounts.
- Keep a fallback: offer to switch language if recognition confidence is low.

## Review checklist

- [ ] Opening line covers required disclosures (AI, recording, business name).
- [ ] Replies capped to short spoken sentences; no lists, links or markdown.
- [ ] Digits, amounts, dates and names are read back before acting.
- [ ] Every state-changing tool confirmed aloud and idempotent server-side.
- [ ] Clear handoff rules and a working transfer tool.
- [ ] Opt-out phrases, silence and interruptions handled.
- [ ] Prompt tested on real calls in each language the agent serves (see `voice-agent-testing`).
