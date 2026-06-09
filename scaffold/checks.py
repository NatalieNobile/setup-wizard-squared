"""Health checks shared by the wizard and doctor.

Every check returns one or more :class:`CheckResult`. The same functions
are called from the wizard (per-step verification) and the doctor (full
report) so validation logic lives in exactly one place. This is the
"doctor-symmetric" principle from ``reference/patterns.md``.

When porting:

1. Replace the example checks at the bottom with your repo's checks.
2. Add a category grouping if you have many checks (the bq_ranger
   reference splits `core` vs `extras` so the doctor can group output).
3. Each check that talks to a network service should accept an optional
   ``timeout`` kwarg — default 10-15s. Long-hung probes break the
   doctor's "fast read-only audit" contract.

Conventions:
    * ``fix_hint`` is required on every ``fail``. The hint must name a
      concrete next action, not generic advice.
    * Checks never prompt. If you need user input, that's a wizard step.
    * Checks are pure read-only audits — they never write files or
      mutate state.
"""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Literal

Severity = Literal["ok", "warn", "fail"]


@dataclass
class CheckResult:
    """One row in the doctor's report.

    ``fix_hint`` is required on every ``fail`` (enforced by convention,
    not the type system). The hint must name the next concrete action —
    "re-run ``./scripts/setup``", not "fix your config".
    """

    name: str
    severity: Severity
    message: str
    fix_hint: str | None = None

    @property
    def ok(self) -> bool:
        return self.severity == "ok"


@dataclass
class DoctorReport:
    """Aggregated checks plus optional structured evidence.

    Add fields here when the wizard needs to consume *typed* values from
    the doctor (e.g. the resolved current-user name, the active project
    id) instead of just severity rows. Keep the field count small —
    most wizards never need more than a half-dozen.
    """

    results: list[CheckResult] = field(default_factory=list)

    @property
    def all_ok(self) -> bool:
        """True iff no check failed (warnings tolerated)."""
        return all(r.severity != "fail" for r in self.results)

    @property
    def any_failures(self) -> bool:
        return any(r.severity == "fail" for r in self.results)

    def add(self, *results: CheckResult) -> None:
        self.results.extend(results)


# ---- generic helpers ----------------------------------------------------


def _run(
    args: list[str],
    *,
    timeout: int = 15,
    input_text: str | None = None,
    env: dict[str, str] | None = None,
) -> tuple[int, str, str]:
    """Run a subprocess and capture ``(returncode, stdout, stderr)``.

    Returns ``(127, "", str(exc))`` if the binary is missing — same
    convention as ``which`` so callers don't need to special-case
    ``FileNotFoundError`` separately from non-zero exit codes. Returns
    ``(124, "", "timed out after Ns")`` on timeout.

    ``env`` lets callers layer dotenv-derived values onto a copy of
    ``os.environ`` so checks against tools that read tokens from env
    (jira-cli, gh, gcloud) work without forcing the user to pre-source.
    """
    try:
        proc = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            input=input_text,
            check=False,
            env=env,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except FileNotFoundError as exc:
        return 127, "", str(exc)
    except subprocess.TimeoutExpired:
        return 124, "", f"timed out after {timeout}s"


def _on_path(name: str) -> bool:
    """True if ``name`` resolves to an executable on the user's PATH."""
    return shutil.which(name) is not None


def is_ssl_trust_failure(message: str) -> bool:
    """True if ``message`` looks like a TLS trust-store error.

    SSL verification failures aren't credential / config / network
    problems — re-prompting the user for tokens or rerunning the check
    would waste their time. Branch on this so the wizard can route to
    a "fix your trust store" remediation block instead of treating it
    as a generic auth failure.

    Patterns cover every flavor of "I couldn't verify the server cert"
    surfaced by urllib, requests, curl, openssl on macOS / Linux. We
    don't detect *valid* certs rejected for other reasons (expiry,
    hostname mismatch) — those are real network problems and a generic
    "check VPN" hint is correct.
    """
    return (
        "CERTIFICATE_VERIFY_FAILED" in message
        or "[SSL:" in message
        or "SSL certificate problem" in message
        or "unable to get local issuer certificate" in message
        or "self-signed certificate" in message
    )


def has_ssl_trust_failure(results: Iterable["CheckResult"]) -> bool:
    """True iff any non-OK result in ``results`` looks like an SSL trust error."""
    return any(
        r.severity != "ok" and is_ssl_trust_failure(r.message)
        for r in results
    )


# ---- example check functions (replace these per repo) -------------------
#
# These are scaffolding examples showing the conventions. Delete them
# and write your own. The doctor's entry point in `doctor.py` registers
# the check functions it should call.


def example_check_python() -> list[CheckResult]:
    """Example: confirm ``python3`` is on PATH. Replace with your own checks."""
    if not _on_path("python3"):
        return [
            CheckResult(
                "python3",
                "fail",
                "not on PATH",
                fix_hint="install Python 3.10+ from https://www.python.org/downloads/",
            )
        ]
    rc, out, _ = _run(["python3", "--version"], timeout=5)
    if rc != 0:
        return [
            CheckResult(
                "python3",
                "fail",
                "python3 found but `python3 --version` failed",
                fix_hint="reinstall Python from https://www.python.org/downloads/",
            )
        ]
    return [CheckResult("python3", "ok", out.strip())]
