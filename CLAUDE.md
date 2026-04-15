# COREcare v2 — Claude Code Agent Config

Read [`CONTRIBUTING.md`](CONTRIBUTING.md) first.

Project-specific docs:
- [`docs/developer/ARCHITECTURE.md`](docs/developer/ARCHITECTURE.md) — codebase patterns
- [`docs/developer/TESTING.md`](docs/developer/TESTING.md) — test tools and conventions
- [`docs/developer/SAFETY.md`](docs/developer/SAFETY.md) — project-specific safety rules
- [`docs/developer/code-review-lenses.md`](docs/developer/code-review-lenses.md) — tech-specific review checklists
- [`docs/developer/project-context.md`](docs/developer/project-context.md) — project-specific persona knowledge

## Shared Claude Code magic

This project inherits shared hooks and scripts from [`suniljames/dotfiles`](https://github.com/suniljames/dotfiles). `.claude/settings.json` references hooks at `$HOME/.claude/hooks/*` with graceful no-op fallback if dotfiles isn't installed on the machine.

To activate hooks locally:

```bash
git clone https://github.com/suniljames/dotfiles.git ~/Code/dotfiles
cd ~/Code/dotfiles && ./install.sh
```

Worktree cleanup runs from the dotfiles-provided script (no local copy needed):

```bash
~/Code/dotfiles/scripts/cleanup_worktrees.py --repo-root "$(git rev-parse --show-toplevel)"
```
