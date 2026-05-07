"""CLI entry point — invoke the rotation runner.

Usage:
  uv run --project scripts/coldreader python -m run [--persona <slug>] [--dry-run]
  uv run --project scripts/coldreader python run.py [--persona <slug>] [--dry-run]

Modes:
  --dry-run         Parser + fixture validation only; no API call. No key required.
  --persona <slug>  Run only this persona (default: all 7 in whitelist order).
  --no-retry        Disable Pass-B extended-thinking retry on a failing question.

The CLI exits 0 on full PASS, 1 on any drift detected, 2 on parser/fixture errors.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from client import MODEL, AnthropicRotationClient
from fixtures import iter_repo_fixtures, load_fixture
from inventory import PERSONAS, extract_index, extract_section
from runner import RotationResult, dry_run_smoke, render_summary_markdown, run_rotation

EXIT_PASS = 0
EXIT_DRIFT = 1
EXIT_SETUP_ERROR = 2

_RUN_TOKEN_INPUT_HARD_CAP = 200_000
_RUN_TOKEN_OUTPUT_HARD_CAP = 30_000


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for ancestor in here.parents:
        if (ancestor / "docs" / "migration" / "v1-pages-inventory.md").exists():
            return ancestor
    raise RuntimeError("Could not locate repo root from CLI module location")


def _select_fixtures(persona: str | None) -> list:  # type: ignore[type-arg]
    if persona is None:
        return list(iter_repo_fixtures())
    if persona not in PERSONAS:
        valid = ", ".join(PERSONAS)
        print(
            f"error: persona {persona!r} not in whitelist; valid: {valid}",
            file=sys.stderr,
        )
        sys.exit(EXIT_SETUP_ERROR)
    fixtures_dir = Path(__file__).resolve().parent / "fixtures"
    return [load_fixture(fixtures_dir / f"{persona}.yaml")]


def _print_summary_to_step_summary(markdown: str) -> None:
    """If running under GitHub Actions, append summary to $GITHUB_STEP_SUMMARY."""
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as f:
            f.write(markdown)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--persona",
        choices=PERSONAS,
        default=None,
        help="run only this persona (default: all 7)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="parser + fixture validation only; no API call",
    )
    parser.add_argument(
        "--no-retry",
        action="store_true",
        help="disable Pass-B extended-thinking retry on a failing question",
    )
    parser.add_argument(
        "--inventory",
        type=Path,
        default=None,
        help="override inventory path (default: detect repo root)",
    )
    args = parser.parse_args(argv)

    inv_path = args.inventory or _repo_root() / "docs" / "migration" / "v1-pages-inventory.md"

    if args.dry_run:
        smoke = dry_run_smoke(inv_path)
        print(
            f"dry-run: loaded {smoke.fixtures_loaded} fixtures; "
            f"{smoke.section_bytes_above_floor} sections above floor; "
            f"errors: {len(smoke.errors)}"
        )
        for err in smoke.errors:
            print(f"  - {err}", file=sys.stderr)
        return EXIT_PASS if not smoke.errors else EXIT_SETUP_ERROR

    try:
        fixtures = _select_fixtures(args.persona)
    except Exception as e:  # noqa: BLE001
        print(f"error loading fixtures: {e}", file=sys.stderr)
        return EXIT_SETUP_ERROR

    try:
        index_text = extract_index(inv_path)
    except Exception as e:  # noqa: BLE001
        print(f"error extracting cross-reference index: {e}", file=sys.stderr)
        return EXIT_SETUP_ERROR

    try:
        client = AnthropicRotationClient()
    except Exception as e:  # noqa: BLE001
        print(f"error initializing Anthropic client: {e}", file=sys.stderr)
        return EXIT_SETUP_ERROR

    results: list[RotationResult] = []
    total_input = 0
    total_output = 0
    for fx in fixtures:
        try:
            section_text = extract_section(inv_path, fx.persona, min_bytes=fx.min_section_bytes)
        except Exception as e:  # noqa: BLE001
            print(f"error extracting section for {fx.persona}: {e}", file=sys.stderr)
            return EXIT_SETUP_ERROR

        result = run_rotation(
            fx,
            section=section_text,
            index=index_text,
            client=client,
            allow_retry=not args.no_retry,
        )
        results.append(result)
        total_input += result.usage.input_tokens
        total_output += result.usage.output_tokens

        if total_input > _RUN_TOKEN_INPUT_HARD_CAP:
            print(
                f"cost guardrail tripped: total uncached input tokens "
                f"{total_input} exceeds {_RUN_TOKEN_INPUT_HARD_CAP}; aborting.",
                file=sys.stderr,
            )
            return EXIT_SETUP_ERROR
        if total_output > _RUN_TOKEN_OUTPUT_HARD_CAP:
            print(
                f"cost guardrail tripped: total output tokens "
                f"{total_output} exceeds {_RUN_TOKEN_OUTPUT_HARD_CAP}; aborting.",
                file=sys.stderr,
            )
            return EXIT_SETUP_ERROR

    run_url = os.environ.get("GITHUB_SERVER_URL", "") and (
        f"{os.environ['GITHUB_SERVER_URL']}/{os.environ.get('GITHUB_REPOSITORY', '')}"
        f"/actions/runs/{os.environ.get('GITHUB_RUN_ID', '')}"
    )
    summary = render_summary_markdown(results, model=MODEL, run_url=run_url or None)
    print(summary)
    _print_summary_to_step_summary(summary)

    return EXIT_DRIFT if any(not r.passed for r in results) else EXIT_PASS


def _main_safe() -> int:
    """Catch unexpected exceptions and surface them as EXIT_SETUP_ERROR (2).

    Without this wrapper, an uncaught exception (network error, API 4xx, bug
    in the runner) exits Python with code 1 — indistinguishable from
    EXIT_DRIFT, which causes the workflow's tracking-issue step to open a
    false drift report. Returning 2 instead routes those failures through
    the setup-error branch where the workflow surfaces a different message.
    """
    try:
        return main()
    except SystemExit:
        raise
    except BaseException as e:  # noqa: BLE001 — top-level safety net
        import traceback

        traceback.print_exc()
        print(
            f"\nrun.py: unhandled {type(e).__name__} — exiting "
            f"with EXIT_SETUP_ERROR ({EXIT_SETUP_ERROR}) so the workflow does "
            "not misclassify this as drift.",
            file=sys.stderr,
        )
        return EXIT_SETUP_ERROR


if __name__ == "__main__":
    sys.exit(_main_safe())
