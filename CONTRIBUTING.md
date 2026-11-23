# Contributing

Thanks for helping developers build voice agents that work on real phone calls. Fixes, new skills, better
checklists and corrections are all welcome.

## Ways to help

- **Fix a fact.** Telephony APIs, realtime models and calling laws change often. If a rule, limit
  or header is out of date, open a PR with a link to the official source.
- **Improve a skill.** Each skill is a folder in `plugins/voice-agents/skills/`
  with a `SKILL.md` (YAML frontmatter `name` + `description`, then instructions).
- **Add a skill.** Same layout. Keep `SKILL.md` under 500 lines; put long
  reference material in a separate file linked from it.
- **Improve the scripts** in `audio-formats/scripts` and `latency-tuning/scripts`.
  They must stay standard-library only and keep their `--self-test` passing.

## Before you open a PR

```bash
python tests/validate_repo.py
python plugins/voice-agents/skills/audio-formats/scripts/voice_audio.py --self-test
python plugins/voice-agents/skills/latency-tuning/scripts/latency_report.py --self-test
```

Code samples must run as written, use test-mode keys only, and treat amounts as
no real phone numbers, recordings or API keys.

## Ground rules

- Accuracy over volume: cite official docs for platform facts.
- Regulatory content is engineering guidance, not legal or tax advice; cite the FCC, TRAI, EU, ICO or provider documentation.
- Never include real API keys, account numbers or personal data.
