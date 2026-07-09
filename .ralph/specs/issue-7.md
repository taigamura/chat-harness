# Skill discovery + slash command pre-processing

> GitHub issue #7 | Labels: ready-for-agent, P0 | https://github.com/taigamura/chat-harness/issues/7

## Parent

#1 Build chat-harness v1: local Qwen+MCP vault assistant

## What to build

Build `skills.py` — the module that discovers vault skills and makes slash commands work reliably.

At startup, `skills.py` scans:
- `<vault>/skills/*/SKILL.md` — reads frontmatter (`name`, `description`, `qwen`, `max_turns`)
- `<vault>/.claude/commands/*.md` — the slash-command registry

Slash command handling (in `__main__.py`):
- Input starting with `/foo args` is detected at the input layer before the model sees it
- Looks up `<vault>/.claude/commands/foo.md`
- Injects its content as an additional system message (via `prompts/skill_wrapper.md` template)
- Runs the normal agent loop with the user's args
- The model never has to "choose" to invoke a skill — it's deterministic

Per-skill reliability flags (read from SKILL.md frontmatter):
- `qwen: skip` → slash command hidden from the REPL (not listed, not invokable)
- `qwen: degraded` → slash command shown but prints a warning banner before running

Also deliver:
- `chat_harness/prompts/system.md` — minimal system prompt: no-JP-translation rule + vault assistant identity
- `chat_harness/prompts/skill_wrapper.md` — template: skill content + user args + "Complete this skill's task using the available MCP tools. When done, stop."

## Acceptance criteria

- [ ] `skills.py` discovers all skills from the vault at startup without error
- [ ] Typing `/brief Tokyo office` in the REPL injects the brief skill and runs the agent loop
- [ ] Skills with `qwen: skip` frontmatter do not appear as available commands
- [ ] Skills with `qwen: degraded` frontmatter print a warning before executing
- [ ] Unknown slash commands (`/doesnotexist`) print a clear error, not a model hallucination
- [ ] System prompt enforces no-Japanese-translation rule

## Blocked by

- #6 REPL + one-shot entry, Rich streaming output

