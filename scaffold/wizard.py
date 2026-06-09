"""``setup-wizard`` — first-run / repair wizard scaffold.

Picker-driven, idempotent, doctor-symmetric. Replace the example step
functions and ``WIZARD_STEPS`` registry with your repo's actual setup
steps. The framework around them — banner, picker dispatch, paced
output, env injection — should not need editing.

Run as a module from the target repo root::

    python3 -m setup.wizard

Or via the bundled launcher::

    ./scripts/setup

Customization checklist:

1. Set ``WIZARD_TITLE`` and ``WIZARD_TAGLINE`` for the banner.
2. Replace ``step_example_*`` with your real step functions. Each
   takes no args and returns ``bool`` (success).
3. Build ``WIZARD_STEPS`` to register them — a list of
   ``(step_id, label, recommended, fn)`` tuples.
4. Update ``COMPLETION_FOOTER_LINES`` with your repo's verify / smoke
   commands.
5. Add module-level helpers (e.g. token-collection prompts) above the
   step functions, mirroring the ``_collect_*`` and ``_print_*_intro``
   pattern.

See ``reference/patterns.md`` in setup-wizard-squared for design
principles. See ``examples/`` for a worked-out wizard.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from collections.abc import Callable

from . import checks
from . import config as cfg
from .prompts import (
    ask,
    ask_secret,
    banner,
    paced_print,
    pick_steps,
    print_results,
    progress_watch,
    step,
    yes_no,
)

# ---- customize per repo -------------------------------------------------

# TODO(setup-wizard): set these to fit the repo.
WIZARD_TITLE: str = "Project Setup"
WIZARD_TAGLINE: str = (
    "Walks you through the prerequisites, credentials, and config files\n"
    "needed to run this project locally. Re-running is always safe."
)

# Lines printed at the end after a successful run. Typically: how to
# verify ("./scripts/doctor"), how to run a smoke test, where to look
# for ongoing usage docs.
COMPLETION_FOOTER_LINES: list[str] = [
    "  Health check:  ./scripts/doctor",
    "  Smoke test:    <fill in your repo's verify command>",
    "  Ongoing docs:  WIZARD_FLOWS.md",
]


# ---- subprocess runners -------------------------------------------------


def _run_interactive(
    args: list[str],
    *,
    timeout: int | None = None,
    env: dict[str, str] | None = None,
) -> int:
    """Run a command with the user's TTY connected — for interactive flows.

    ``timeout`` is passed straight through to ``subprocess.run``. When
    set, a child that outlives it is killed and ``subprocess.TimeoutExpired``
    is raised for the caller to handle. Leave it ``None`` for
    long-running but legitimate launches (``brew install``, ``npm
    install -g``, dependency syncs).

    ``env`` overrides the subprocess's environment when provided. Build
    it by copying ``os.environ`` and layering dotenv values on top so
    child commands like ``jira init`` see ``JIRA_API_TOKEN`` even if
    the user never sourced anything in their shell. **This is the
    "self-contained" principle from reference/patterns.md.**
    """
    print(f"  $ {' '.join(args)}")
    try:
        return subprocess.run(args, check=False, timeout=timeout, env=env).returncode
    except FileNotFoundError:
        print(f"  !! {args[0]} not found on PATH; skipping.")
        return 127


# ---- example step functions (replace these per repo) --------------------
#
# Each step:
#   1. Calls a check function from ``checks.py``.
#   2. Renders the result via ``print_results``.
#   3. Returns early if already OK.
#   4. Otherwise: prompts (if needed), repairs, returns success boolean.
#
# Steps NEVER prompt unconditionally. The picker has already asked
# whether to run this step — once inside, only prompt for things that
# require user input (credentials, install confirmations).


def step_example_preflight() -> bool:
    """Example: verify a system tool is on PATH.

    Replace with your repo's preflight (e.g. ``java -version``,
    ``./gradlew --version``, ``node --version``, etc.).
    """
    step(1, len(WIZARD_STEPS), "preflight (example)")
    print("  Verifies that required system tools are installed.")
    print()
    results = checks.example_check_python()
    print_results(results, show_ok=True)
    return all(r.severity == "ok" for r in results)


def step_example_credential() -> bool:
    """Example: collect a credential and write it to a config file.

    Pattern:
        1. If the value is already on disk + valid, skip.
        2. Otherwise prompt with ``ask_secret`` (hidden input).
        3. Write to a dotenv file with ``cfg.write_dotenv_key``.
        4. Run a verification check; return True on success.
    """
    step(2, len(WIZARD_STEPS), "credential (example)")
    print("  Captures an API token and stores it in a local config file.")
    print()

    # TODO(setup-wizard): replace with the actual file path from cfg.
    # token_file = cfg.SOME_ENV_FILE
    # existing = cfg.read_dotenv(token_file).get("MY_TOKEN", "")
    # if existing:
    #     paced_print("  Token already present.", after_ms=200)
    #     return True

    print("  Generate one at: https://example.com/tokens")
    token = ask_secret("API token", hint="treat like a password; not echoed")
    if not token:
        print("  Skipped (no token entered).")
        return True

    # cfg.write_dotenv_key(token_file, "MY_TOKEN", token)
    # paced_print(f"  → wrote {token_file}", after_ms=200)
    return True


# ---- step registry ------------------------------------------------------
#
# (step_id, label, recommended, fn). Order here is the order steps run
# in. The picker uses these tuples to render the menu; ``run_steps``
# uses them to dispatch the user's selection.

WizardStepFn = Callable[[], bool]
WIZARD_STEPS: list[tuple[str, str, bool, WizardStepFn]] = [
    # TODO(setup-wizard): register your real step functions here.
    ("preflight", "preflight (example)", True, step_example_preflight),
    ("credential", "credential (example)", True, step_example_credential),
]


# ---- runner -------------------------------------------------------------


def _selected_step_indices(selected_ids: list[str]) -> list[int]:
    """Map selected step ids back to their 1-based positions in WIZARD_STEPS."""
    by_id = {sid: i for i, (sid, _, _, _) in enumerate(WIZARD_STEPS, 1)}
    return [by_id[sid] for sid in selected_ids if sid in by_id]


def run_steps(selected_ids: list[str]) -> int:
    """Run the picked steps in canonical order. Returns process exit code.

    Each step's failure is reported but does not abort the run — users
    often want to push through several optional steps even if one
    failed. The doctor pattern means they can re-run individually.
    """
    if not selected_ids:
        paced_print("  Nothing selected. Exiting.", after_ms=200)
        return 0

    paced_print(
        f"  → Will set up: {', '.join(sid for sid in selected_ids)}",
        after_ms=200,
    )

    failures: list[str] = []
    for sid, _label, _recommended, fn in WIZARD_STEPS:
        if sid not in selected_ids:
            continue
        try:
            ok = fn()
        except KeyboardInterrupt:
            print("\n  Interrupted by user.")
            return 130
        except Exception as exc:  # noqa: BLE001 - intentional broad catch
            print(f"  [FAIL] step `{sid}` raised {type(exc).__name__}: {exc}")
            failures.append(sid)
            continue
        if not ok:
            failures.append(sid)

    print()
    banner(f"{WIZARD_TITLE} complete")
    for line in COMPLETION_FOOTER_LINES:
        paced_print(line, after_ms=80)

    if failures:
        print()
        print(f"  {len(failures)} step(s) reported issues: {', '.join(failures)}")
        print("  Re-run `./scripts/setup` and pick those steps to retry.")
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    """Entry point. Renders the picker, runs selected steps, prints footer."""
    argv = list(argv if argv is not None else sys.argv[1:])

    banner(WIZARD_TITLE)
    paced_print(*WIZARD_TAGLINE.splitlines(), after_ms=300)
    print()

    picker_items = [(sid, label, recommended) for sid, label, recommended, _ in WIZARD_STEPS]
    selected = pick_steps(picker_items)
    print()

    return run_steps(selected)


if __name__ == "__main__":
    raise SystemExit(main())
