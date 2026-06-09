"""``doctor`` — read-only environment audit.

Calls every registered check function and prints results. Same
``CheckResult`` rendering as the wizard, so the user gets the same
``[OK]`` / ``[WARN]`` / ``[FAIL]`` glyphs from both surfaces.

Exits non-zero only on hard failures. Warnings are tolerated — they
mean "optional thing isn't set up" rather than "your environment is
broken". Tune ``DOCTOR_FAIL_ON_WARN`` per repo if your audience needs
strict exit codes.
"""

from __future__ import annotations

import sys
from collections.abc import Callable

from . import checks
from .checks import CheckResult, DoctorReport
from .prompts import banner, paced_print, print_results

# ---- customize per repo -------------------------------------------------

DOCTOR_TITLE: str = "Doctor"
DOCTOR_TAGLINE: str = (
    "Read-only audit. Re-runs every step's check function and prints results."
)

# True if any [WARN] should make the doctor exit non-zero. Default
# False (warnings are tolerated). Flip for strict CI gates.
DOCTOR_FAIL_ON_WARN: bool = False

# Registered check functions. Each returns a list[CheckResult]. Order
# determines display order. TODO: replace with your real checks from
# checks.py.
CheckFn = Callable[[], list[CheckResult]]
DOCTOR_CHECKS: list[CheckFn] = [
    checks.example_check_python,
]


# ---- runner -------------------------------------------------------------


def run_all_checks() -> DoctorReport:
    """Call every registered check and assemble a ``DoctorReport``."""
    report = DoctorReport()
    for check in DOCTOR_CHECKS:
        try:
            results = check()
        except Exception as exc:  # noqa: BLE001 - keep the doctor robust
            results = [
                CheckResult(
                    name=check.__name__,
                    severity="fail",
                    message=f"check raised {type(exc).__name__}: {exc}",
                    fix_hint="report this as a doctor bug.",
                )
            ]
        report.add(*results)
    return report


def main(argv: list[str] | None = None) -> int:
    """Entry point. Prints banner, runs all checks, returns exit code."""
    argv = list(argv if argv is not None else sys.argv[1:])

    banner(DOCTOR_TITLE)
    paced_print(DOCTOR_TAGLINE, after_ms=300)
    print()

    report = run_all_checks()
    print_results(report.results, show_ok=True, show_fix=True)

    print()
    fails = sum(1 for r in report.results if r.severity == "fail")
    warns = sum(1 for r in report.results if r.severity == "warn")
    oks = sum(1 for r in report.results if r.severity == "ok")
    paced_print(f"  Summary: {oks} OK, {warns} WARN, {fails} FAIL", after_ms=150)

    if fails > 0:
        return 1
    if DOCTOR_FAIL_ON_WARN and warns > 0:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
