# COREcare v2 — Claude Code

> **Read [`AGENTS.md`](AGENTS.md) first.** This file carries only what's unique to Claude Code; shared agent guidance (verify, don't-touch, repo map, conventions, glossary) lives in `AGENTS.md`.

You are the **builder** agent for this repo (per the [engineering team manifest](https://github.com/suniljames/directives/blob/main/teams/engineering/manifest.yml) — all roles where `agent: builder`). When operating without an orchestrator, assume validator roles as separate review passes.

## Pipeline commands

The slash-commands in [`.claude/commands/`](.claude/commands/) — `/define`, `/design`, `/implement`, `/review`, `/summarize` — are Claude-specific and will not work in other AI tools.

## Shared Claude Code magic

This project inherits hooks and scripts from [`suniljames/dotfiles`](https://github.com/suniljames/dotfiles). `.claude/settings.json` references hooks at `$HOME/.claude/hooks/*` with graceful no-op fallback if dotfiles isn't installed on the machine.

To activate hooks locally:

```bash
git clone https://github.com/suniljames/dotfiles.git ~/Code/dotfiles
cd ~/Code/dotfiles && ./install.sh
```

Worktree cleanup runs from the dotfiles-provided script (no local copy needed):

```bash
~/Code/dotfiles/scripts/cleanup_worktrees.py --repo-root "$(git rev-parse --show-toplevel)"
```
