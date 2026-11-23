# Security policy

## Reporting a vulnerability

Please report security problems privately through
[GitHub security advisories](https://github.com/Viprasol-Tech/claude-voice-agent-skills/security/advisories/new)
or by email to [support@viprasol.com](mailto:support@viprasol.com). Do not open a public issue.
We aim to reply within 3 working days.

## Scope

- The bundled scripts (`voice_audio.py`, `latency_report.py`): they read
  local audio or log files and print results. They make no network calls and run no
  shell commands.
- Skill instructions that could lead an assistant to weaken caller privacy or
  safety: recording without notice, capturing card numbers by voice, unauthorised voice cloning.

## Keep secrets and card data out of chats

These skills never need real customer data. Never paste real call recordings,
transcripts with personal data, phone numbers, API keys or provider auth tokens
into an issue, pull request or chat. Use synthetic data and sandbox keys. If a key has been
exposed, rotate it with your provider immediately.
