# Worked example: box-java-sdk

A real wizard, built using this repo's scaffold, applied to the
[box/box-java-sdk](https://github.com/box/box-java-sdk) public Java
SDK.

- **Upstream PR**: [box/box-java-sdk#1878](https://github.com/box/box-java-sdk/pull/1878) (draft)
- **Fork**: [NatalieNobile/box-java-sdk](https://github.com/NatalieNobile/box-java-sdk/tree/feat/setup-wizard)

## What this example demonstrates

A 3-step wizard for a multi-auth-mode SDK:

1. **Java + Gradle preflight** (`step_preflight` in `setup/wizard.py`)
2. **Auth credentials** (`step_auth_credentials`) — inner picker for
   Developer Token / JWT / Client Credentials / OAuth, then captures
   the right state for each.
3. **Smoke test snippet** (`step_smoke_test`) — prints a 4-line Java
   program keyed to the chosen auth mode.

Plus a doctor (`setup/doctor.py`) that re-runs each step's check
function:

```text
=======================
= Box Java SDK doctor =
=======================
  [OK]   java: JDK 19 (java version "19.0.1" 2022-10-18)
  [OK]   gradle: Gradle 8.10.1
  [OK]   box-config: auth mode = developer_token
  [OK]   developer-token: token set (64 chars). Note: tokens expire after 60 min.
  [OK]   jwt-config: n/a (other auth mode)

  Summary: 5 OK, 0 WARN, 0 FAIL
```

## Files

| Path | Customized? |
| --- | --- |
| `setup/prompts.py` | No — verbatim from `scaffold/prompts.py` |
| `setup/config.py` | Yes — `PROJECT_NAME = "box-java-sdk"`, added auth-mode + URL constants |
| `setup/checks.py` | Yes — replaced example check with `check_java`, `check_gradle`, `check_box_config`, `check_developer_token`, `check_jwt_config` |
| `setup/wizard.py` | Yes — three step functions + auth-mode sub-picker + per-mode credential collectors |
| `setup/doctor.py` | Light — registered the new check functions |
| `setup/__init__.py` | No |
| `scripts/setup`, `scripts/doctor` | No |
| `WIZARD_FLOWS.md` | Generated from `reference/docs-template.md`, customized for the 3-step flow |
| `box-config.properties.example` | New — annotated template the wizard's output mirrors |

## Patterns this exercises

| Principle from `reference/patterns.md` | Where you see it |
| --- | --- |
| Self-contained | Wizard reads `box-config.properties` itself; never asks user to source. |
| Idempotent | Step 2 detects existing `box.auth.mode` and asks "re-collect / change?" |
| Paced output | All explainer blocks use `paced_print(..., after_ms=N)`. |
| Picker-first | Top-level 3-step picker + inner 4-mode auth picker. |
| Doctor-symmetric | Every step has a `check_*` function the doctor calls. |
| Env injection | `_run_interactive(args, env=...)` available; not exercised by step 3 (which is print-only) but ready for future "run gradle test" extensions. |
| Progress watchdog | Not exercised in this 3-step flow (no long-running subprocess). The scaffold's `progress_watch` is available if you add one. |

## How to apply this scaffold to a new repo

See [`SKILL.md`](../../SKILL.md) at the repo root. The short version:

1. Survey the target repo using [`reference/repo-survey.md`](../../reference/repo-survey.md).
2. Copy `scaffold/` into the target.
3. Customize `wizard.py`, `checks.py`, `config.py` per repo.
4. Generate `WIZARD_FLOWS.md` from [`reference/docs-template.md`](../../reference/docs-template.md).
5. Drop a copy of the customized files into a new `examples/<repo-name>/` here, mirroring this example.
