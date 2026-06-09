# scaffold/

Drop-in Python the agent copies into a target repo and customizes.

## Files

| File           | Customize?                                                             |
| -------------- | ---------------------------------------------------------------------- |
| `prompts.py`   | **No** — TTY primitives. Edits here mean you found a bug. Report it.  |
| `config.py`    | **Yes** — set `PROJECT_NAME`, add repo-specific config-file paths.    |
| `checks.py`    | **Yes** — replace example check with real ones. Keep helpers as-is.   |
| `wizard.py`    | **Yes** — heart of the customization. Replace `step_example_*` and `WIZARD_STEPS`. |
| `doctor.py`    | **Light edit** — register your check functions in `DOCTOR_CHECKS`.    |
| `__init__.py`  | **No** — package marker.                                               |
| `scripts/setup` | **Maybe** — bash launcher. Edit only if your repo has a non-standard Python setup. |
| `scripts/doctor` | **Maybe** — same.                                                    |

## Drop-in steps

From the target repo root:

```bash
mkdir -p setup scripts
cp /path/to/setup-wizard-squared/scaffold/{prompts,config,checks,wizard,doctor,__init__}.py setup/
cp /path/to/setup-wizard-squared/scaffold/scripts/{setup,doctor} scripts/
chmod +x scripts/{setup,doctor}
```

Smoke test:

```bash
python3 -c "from setup import wizard, doctor"   # both should import cleanly
./scripts/doctor                                  # should report the example check passing
./scripts/setup                                   # walks the example wizard
```

When that's working, start customizing per [`reference/repo-survey.md`](../reference/repo-survey.md).

## Required Python version

Python 3.10+. The scaffold uses PEP 604 union types (`int | None`) and
parenthesized `with` statements. If your target repo must support
older Python, either:

- pin a `python3.10+` requirement in the launcher (the cleanest path),
- or rewrite the unions to `Optional[X]` / `Union[X, Y]` and add
  `from __future__ import annotations` everywhere.

## What does NOT belong in the scaffold

These are intentionally **out of scope** — they're repo-specific or
cross-cutting concerns the scaffold doesn't try to solve:

- **Cloud SDK auth flows** (gcloud, AWS, Azure). Each has its own CLI
  and dance; reach for that CLI's native onboarding when one exists.
- **Browser-based OAuth** loopback servers. The bq_ranger reference
  has a `_run_browser_auth` helper with a 2-min timeout; copy it if
  you need that pattern.
- **Package-manager-specific config** (`.npmrc`, JFrog auth, custom
  Maven repos). Add per-repo as needed.
- **Encrypted secrets** beyond owner-only chmod. If your repo needs
  GPG / age / SOPS, layer that on top.

When you find yourself adding one of these to the scaffold itself,
stop and add it as an `examples/` worked example instead — that keeps
the scaffold lean and discoverable.
