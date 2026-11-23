#!/usr/bin/env python3
"""Validate the marketplace, the plugin and every skill.

Part of claude-trading-skills by Viprasol Tech Private Limited.
Standard library only. Exit code 0 = valid, 1 = problems found.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
LINK_RE = re.compile(r"\]\(([^)\s]+)\)")
SECRET_RE = re.compile(r"(AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----|sk-[A-Za-z0-9]{32,})")
MAX_DESCRIPTION = 1024  # portable limit for skills outside Claude Code
MAX_SKILL_LINES = 500

errors: list[str] = []


def fail(msg: str) -> None:
    errors.append(msg)


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"{path.relative_to(ROOT)}: {exc}")
        return {}


def frontmatter(text: str) -> dict[str, str] | None:
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end == -1:
        return None
    fields: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" in line and not line.startswith((" ", "\t", "#")):
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()
    return fields


def check_links(md: Path) -> None:
    for target in LINK_RE.findall(md.read_text(encoding="utf-8")):
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        if not (md.parent / target.split("#")[0]).exists():
            fail(f"{md.relative_to(ROOT)}: broken link -> {target}")


def check_skill(skill_dir: Path) -> None:
    rel = skill_dir.relative_to(ROOT)
    md = skill_dir / "SKILL.md"
    if not md.is_file():
        fail(f"{rel}: missing SKILL.md")
        return
    text = md.read_text(encoding="utf-8")
    fm = frontmatter(text)
    if fm is None:
        fail(f"{rel}/SKILL.md: frontmatter must start on line 1 and be closed with ---")
        return
    name, desc = fm.get("name", ""), fm.get("description", "")
    if name != skill_dir.name:
        fail(f"{rel}/SKILL.md: name '{name}' must equal the folder name '{skill_dir.name}'")
    if not NAME_RE.match(name or "-"):
        fail(f"{rel}/SKILL.md: name must be lowercase letters, digits and hyphens")
    if len(desc) < 80:
        fail(f"{rel}/SKILL.md: description is missing or too short to trigger reliably")
    if len(desc) > MAX_DESCRIPTION:
        fail(f"{rel}/SKILL.md: description is {len(desc)} chars (max {MAX_DESCRIPTION})")
    if text.count("\n") > MAX_SKILL_LINES:
        fail(f"{rel}/SKILL.md: over {MAX_SKILL_LINES} lines; move detail to a reference file")
    for script in re.findall(r"\$\{CLAUDE_SKILL_DIR\}/([\w./-]+\.py)", text):
        if not (skill_dir / script).resolve().is_file():
            fail(f"{rel}/SKILL.md: referenced script not found: {script}")
    for f in skill_dir.rglob("*"):
        if f.is_file() and f.suffix in {".md", ".py", ".pine", ".mq5"}:
            if SECRET_RE.search(f.read_text(encoding="utf-8")):
                fail(f"{f.relative_to(ROOT)}: looks like it contains a secret")
            if f.suffix == ".md":
                check_links(f)


def main() -> int:
    market = load_json(ROOT / ".claude-plugin" / "marketplace.json")
    for key in ("name", "owner", "plugins"):
        if key not in market:
            fail(f"marketplace.json: missing '{key}'")
    skills_seen = 0
    for entry in market.get("plugins", []):
        src = entry.get("source", "")
        if not str(src).startswith("./") or ".." in str(src):
            fail(f"marketplace.json: plugin source must be a ./relative path: {src}")
            continue
        plugin_dir = ROOT / src
        manifest = load_json(plugin_dir / ".claude-plugin" / "plugin.json")
        pname = manifest.get("name", "")
        if pname != entry.get("name"):
            fail(f"{src}: plugin.json name '{pname}' differs from marketplace entry '{entry.get('name')}'")
        if not NAME_RE.match(pname or "-") or pname.startswith(("claude-", "anthropic-")):
            fail(f"{src}: invalid or reserved plugin name '{pname}'")
        skills_root = plugin_dir / "skills"
        if not skills_root.is_dir():
            fail(f"{src}: no skills/ folder")
            continue
        for skill_dir in sorted(p for p in skills_root.iterdir() if p.is_dir()):
            check_skill(skill_dir)
            skills_seen += 1
    for md in [ROOT / "README.md", ROOT / "CONTRIBUTING.md", ROOT / "SUPPORT.md"]:
        if md.exists():
            check_links(md)
    for f in [*ROOT.glob("*.md"), *ROOT.glob("install.*"), *(ROOT / ".github").rglob("*.yml")]:
        if SECRET_RE.search(f.read_text(encoding="utf-8")):
            fail(f"{f.relative_to(ROOT)}: looks like it contains a secret")
    if skills_seen == 0:
        fail("no skills found")
    if errors:
        print("\n".join(f"FAIL {e}" for e in errors))
        return 1
    print(f"OK: marketplace, plugin and {skills_seen} skills are valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
