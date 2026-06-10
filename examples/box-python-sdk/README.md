# Worked example — `box/box-python-sdk` (Box Python SDK v10)

A real, end-to-end application of the `setup-wizard-squared` scaffold
to the [Box Python SDK v10](https://github.com/box/box-python-sdk).
This is the Python sibling to the [`box-java-sdk`
example](../box-java-sdk/) — same scaffold, same picker grammar, same
auth-mode coverage, different ecosystem.

**Upstream draft PR:** https://github.com/box/box-python-sdk/pull/1475

## What this demonstrates

- The same 7 patterns (paced output, picker-first, env injection,
  doctor-symmetry, idempotence, progress watchdog, self-contained
  credential capture) ported from `bq_ranger` produce a wizard that
  fits a totally different language ecosystem (Python / pip /
  setup.py) without scaffold changes.
- A 3-step picker (preflight, auth credentials, smoke snippet) is
  enough scope for an SDK setup wizard. Same step count as
  `box-java-sdk`.
- The same 4-way auth-mode picker (Developer Token / JWT / CCG /
  OAuth) works across ecosystems — only the credential storage format
  (`.env` vs Java `.properties`) and snippet language differ.

## Files

| Path                  | Source                                  | What changed                                                            |
| --------------------- | --------------------------------------- | ----------------------------------------------------------------------- |
| `dev_setup/prompts.py` | scaffold (verbatim)                    | none — generic TTY primitives                                           |
| `dev_setup/config.py`  | scaffold (customized)                  | `PROJECT_NAME`, `BOX_ENV_FILE`, `MIN_PYTHON`, auth-mode constants       |
| `dev_setup/checks.py`  | scaffold (replaced example)            | `check_python`, `check_pip`, `check_sdk_importable`, `check_box_env`, `check_developer_token`, `check_jwt_config` |
| `dev_setup/wizard.py`  | scaffold (replaced steps)              | 3 real steps: preflight (with optional `pip install -e .[test,dev]`), auth-credentials picker, smoke-test snippet |
| `dev_setup/doctor.py`  | scaffold (registered checks)           | `DOCTOR_CHECKS` list points at the 6 real checks                        |
| `scripts/setup`, `scripts/doctor` | scaffold (verbatim)         | bash launchers (`python3 -m dev_setup.wizard` etc.)                     |
| `WIZARD_FLOWS.md`      | template (filled in)                   | Mermaid decision tree, step table, recovery paths, auth-mode table      |
| `.env.example`         | new                                    | annotated template the user copies / replaces with `./scripts/setup`    |

## Why `dev_setup/` and not `setup/`

Python's `setup.py` lives at the repo root and `setuptools.find_packages()`
walks the source tree looking for anything with `__init__.py`. Naming
the wizard package `setup/` would create two ambiguities:

1. Import resolution between the script `setup.py` and a package
   `setup/` is environment-specific.
2. `find_packages()` would happily ship the wizard as a top-level
   package called `setup` when a user runs `pip install boxsdk`.

Renaming to `dev_setup/` removes both ambiguities. A one-line addition
to `setup.py` (`exclude=['docs', '*test*', 'dev_setup', 'dev_setup.*']`)
keeps the package out of the pip distribution belt-and-braces.

This is the only scaffold concession to Python's ecosystem; everything
else carries over unchanged.

## Patterns exercised

- **Paced output** — `WIZARD_PACE_MS` env var (`0` for CI / scripted
  onboarding, default `80`).
- **Picker-first** — top-level 3-step picker accepts
  `1,3` / `1-3` / `all` / `recommended` / `none` / blank. Auth-mode
  step has its own inner 4-way picker.
- **Env injection** — `_run_interactive(env=...)` lets the wizard
  layer `.env` values onto the subprocess environment before invoking
  `pip` etc. (also used in step 1's editable install).
- **Doctor-symmetry** — every step has a check function in `checks.py`
  the doctor calls. Re-running `./scripts/doctor` after the wizard
  shows everything in one shot.
- **Idempotence** — re-running the wizard with an existing `.env`
  prompts to keep or change the auth mode rather than wiping it.
- **Progress watchdog** — `pip install -e .[test,dev]` is wrapped so
  the user sees `current action: installing SDK in editable mode (pip)`
  if it runs longer than 5s.
- **Self-contained** — the wizard reads `.env` itself when computing
  the smoke snippet and the doctor's mode-specific checks. Users never
  need to "first source X".

## Try it

```bash
git clone https://github.com/NatalieNobile/box-python-sdk.git -b feat/setup-wizard
cd box-python-sdk
./scripts/setup           # 3-step picker
./scripts/doctor          # read-only audit afterwards
```

The branch on the fork is what was opened as the upstream draft PR.

## Provenance

This example was synthesized from `bq_ranger`'s setup wizard and the
[`setup-wizard-squared`](../../) scaffold. Patterns and design
rationale live in [`reference/patterns.md`](../../reference/patterns.md).
