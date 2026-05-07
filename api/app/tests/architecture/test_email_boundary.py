"""Architecture-fitness test for the outbound-email boundary (issue #120).

Rule: only modules under app.services.email.* may import a transport SDK or
instantiate a transport class directly. Any other module reaching past the
boundary is a regression to v1's two-path divergence.

Removing or weakening this test requires a new ADR (per the issue).
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

# Modules whose import is the v1 footgun we are designing out.
FORBIDDEN_TRANSPORT_MODULES = {
    "sendgrid",
    "smtplib",
    # Direct transport classes also flagged if imported outside the boundary.
    "app.services.email.transports",
}

# Public symbols feature code is allowed to import from app.services.email.
ALLOWED_PUBLIC_API = {
    "EmailSender",
    "EmailValidationError",
    "IdempotencyConflict",
    "SendRequest",
    "SendResult",
    "make_email_sender",
    "render_subjects",
}

APP_ROOT = Path(__file__).resolve().parents[2]  # api/app


def _iter_python_files() -> list[Path]:
    paths: list[Path] = []
    for p in APP_ROOT.rglob("*.py"):
        rel = p.relative_to(APP_ROOT)
        parts = rel.parts
        # Skip tests — they are allowed to import the email package internals
        # to verify behavior.
        if parts and parts[0] == "tests":
            continue
        # Skip the email package itself — sender.py imports transports.py,
        # and that is the legitimate inside-the-boundary case.
        if parts[:2] == ("services", "email"):
            continue
        paths.append(p)
    return paths


def _imports_in(path: Path) -> list[tuple[str, str | None]]:
    """Return (module, name) pairs for every Import / ImportFrom in `path`."""
    tree = ast.parse(path.read_text(), filename=str(path))
    out: list[tuple[str, str | None]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                out.append((alias.name, None))
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            for alias in node.names:
                out.append((mod, alias.name))
    return out


@pytest.mark.parametrize("py_file", _iter_python_files(), ids=lambda p: str(p))
def test_no_module_outside_email_imports_a_transport(py_file: Path) -> None:
    """No module outside app.services.email.* may import sendgrid, smtplib, or
    app.services.email.transports."""
    for mod, name in _imports_in(py_file):
        # `import sendgrid` / `import smtplib` / `import app.services.email.transports`
        if mod in FORBIDDEN_TRANSPORT_MODULES:
            pytest.fail(
                f"{py_file} imports forbidden transport module '{mod}'. "
                f"All outbound email must go through app.services.email.EmailSender."
            )
        # `from app.services.email.transports import X`
        if mod == "app.services.email.transports":
            pytest.fail(
                f"{py_file} imports from app.services.email.transports directly. "
                f"Use EmailSender; do not call transports yourself."
            )


@pytest.mark.parametrize("py_file", _iter_python_files(), ids=lambda p: str(p))
def test_email_imports_use_only_allowed_public_api(py_file: Path) -> None:
    """Modules outside app.services.email.* importing from the package may only
    use the documented public API."""
    for mod, name in _imports_in(py_file):
        if not mod.startswith("app.services.email"):
            continue
        # Top-level package import is fine; check the symbol if any.
        if name is None:
            continue
        if name not in ALLOWED_PUBLIC_API:
            pytest.fail(
                f"{py_file} imports private/internal symbol '{name}' from "
                f"'{mod}'. Public API: {sorted(ALLOWED_PUBLIC_API)}."
            )
