---
name: setup-wizard
description: >-
  Use when a user asks for a setup wizard, onboarding script, first-run
  installer, or "doctor" command for a repo. Walks the agent through
  surveying the target repo, copying a Python scaffold into it, customizing
  step functions for the repo's actual tools and secrets, and generating
  user-facing docs (decision tree + step table). Optimized for repos that
  collect Personal Access Tokens, API keys, OAuth/JWT credentials, or
  developer tokens during onboarding.
---

# setup-wizard

## Overview

A repo's first-run experience is the highest-leverage UX surface it has —
every onboarding friction point compounds across hundreds of contributors.
This skill encodes a hardened wizard pattern (paced output, idempotent
steps, picker-based selection, env injection, doctor-symmetric checks)
that you adapt to the target repo, instead of writing one from scratch
every time.

The wizard you produce should let a user clone the repo and run `./setup`
and have a working environment when it finishes — **no separate "first
source this file" or "first export that token" steps**. The scaffold
makes that bar reachable.

## When to Use

Trigger on any of:

- "Build a setup wizard for repo X."
- "Make onboarding less painful in repo Y."
- "We need a doctor command that checks the dev environment."
- "Users keep skipping step N of our README."
- "I want a guided way to enter our API keys / PATs / credentials."
- The target repo has a multi-paragraph "Getting Started" section that
  collects more than two pieces of state from the user.

Skip the skill when:

- The repo already has a wizard you can edit instead — read the existing
  one and apply patterns from `reference/patterns.md` to it inline.
- The need is a one-off shell script that runs three commands. A wizard
  is overhead for trivial onboarding.
- The user asks for a CI/build tool. This skill is for human onboarding,
  not pipeline automation.

## Core Pattern

The skill is survey-first. Do not start writing code until you can answer
every question in `reference/repo-survey.md`. Most wizard pain comes from
guessing at step boundaries before reading the repo.

### 1. Survey the target repo

Read these in order and record findings in `reference/repo-survey.md`:

| Source                      | What you're looking for                                                  |
| --------------------------- | ------------------------------------------------------------------------ |
| `README.md` "Getting Started" | The canonical onboarding flow the user already documents.              |
| `CONTRIBUTING.md`           | Dev-environment expectations beyond end-user onboarding.                 |
| `.env.example` / `*.env*`   | Existing convention for configuration files and what keys live in them. |
| Build files (`pom.xml`, `build.gradle`, `package.json`, `pyproject.toml`, `Cargo.toml`, etc.) | Required language runtime, package manager, test runner. |
| `.tool-versions` / `.nvmrc` / etc. | Pinned tool versions the wizard should validate.                  |
| Source tree                 | Auth flows already implemented (OAuth, JWT, API key, etc.) — these are the wizard's choices. |

### 2. Decide step boundaries

A good wizard is 3–7 steps. Each step:

- Has a single clear deliverable (one file written, one tool installed,
  one credential captured).
- Has a check function the doctor can re-run without prompting.
- Is independently re-runnable — re-running just verifies and skips.
- Maps to one row in the picker.

Avoid "kitchen sink" steps that bundle "install + configure + verify +
test" — split them. Combining them makes failures hard to recover from.

### 3. Copy the scaffold

```bash
mkdir -p <target-repo>/setup
cp scaffold/{prompts,config,checks,wizard,doctor}.py <target-repo>/setup/
cp scaffold/__init__.py <target-repo>/setup/
mkdir -p <target-repo>/scripts
cp scaffold/scripts/{setup,doctor} <target-repo>/scripts/
chmod +x <target-repo>/scripts/{setup,doctor}
```

Adjust paths if the target repo has its own `scripts/` or `bin/`
convention. The scaffold's Python files are import-clean — they don't
reference each other by hardcoded paths, so they relocate freely.

### 4. Customize step functions

Open `setup/wizard.py` in the target. The `TODO` markers identify
exactly where to add repo-specific logic:

```python
# TODO(setup-wizard): add your step functions here, registering each in
# WIZARD_STEPS with (step_id, label, recommended, fn) tuples. See
# reference/patterns.md for the step function shape.
```

Each step function takes no args and returns `bool` (success). It calls
helpers from `prompts` and `checks`. See `examples/` for a full
worked-out wizard.

### 5. Generate user-facing docs

Use `reference/docs-template.md` as the starting point for a
`WIZARD_FLOWS.md` (or `docs/SETUP.md`) in the target repo. Fill in:

- The Mermaid decision tree (one node per step + the picker).
- A step table (id, label, what it checks, what it writes, recommended).
- A recovery table (common failure modes and what to do).
- Cross-cutting features the user should know about (pacing env var,
  picker grammar, doctor command).

### 6. Self-test

Before claiming the wizard is done:

- Run `python -c "from setup import wizard, doctor"` from the target
  repo root — both should import cleanly.
- Run the doctor against an unconfigured machine state — every check
  should return a `WARN` or `FAIL` with an actionable fix hint.
- Run the wizard and walk through the picker selecting `none` — it
  should exit cleanly without side effects.
- Run the wizard, select `recommended`, and complete the flow — the
  doctor should then report all `OK`.

## Quick Reference

### The seven design principles

These come from `reference/patterns.md`. Brief table — read the full
reference before customizing.

| Principle           | Why it matters                                              |
| ------------------- | ----------------------------------------------------------- |
| Self-contained      | Cloning the repo is the only prerequisite.                  |
| Idempotent          | Re-running is always safe; steps detect prior success.      |
| Paced output        | Walls of text become readable; tunable via `WIZARD_PACE_MS`. |
| Picker-first        | Users skip what they don't need.                            |
| Doctor-symmetric    | Every step has a check the doctor can re-run.               |
| Env injection       | Wizard reads tokens itself, never says "go source this".    |
| Progress watchdog   | Long commands print "current action" so they don't look hung. |

### Scaffold file map

| File                     | Lines (approx) | Purpose                                                                        |
| ------------------------ | -------------- | ------------------------------------------------------------------------------ |
| `scaffold/prompts.py`    | ~350           | Paced output, picker, yes/no, getpass wrapper, progress watchdog, results printer. |
| `scaffold/config.py`     | ~150           | Read/write dotenv, atomic file writers, owner-only chmod.                      |
| `scaffold/checks.py`     | ~180           | `CheckResult` dataclass, `_on_path`, `_run`, SSL-trust failure detector.       |
| `scaffold/wizard.py`     | ~220           | Banner, step framework, picker dispatch, `_run_interactive` with env injection. |
| `scaffold/doctor.py`     | ~50            | Loops registered check functions, prints results.                              |
| `scaffold/__init__.py`   | ~5             | Package marker.                                                                |
| `scaffold/scripts/setup` | ~10            | Bash launcher: `exec python3 -m setup.wizard "$@"`.                            |
| `scaffold/scripts/doctor` | ~10           | Bash launcher: `exec python3 -m setup.doctor "$@"`.                            |

Total scaffold cost: ~970 lines. The repo-specific customization is
typically another 200–400 lines on top.

### What the agent always does

1. **Read first.** Survey the target repo before writing any code.
2. **One step = one outcome.** No bundled steps.
3. **Doctor before wizard.** Write the check function, then the step that
   uses it. Steps without checks rot fast.
4. **Env injection over shell sourcing.** When a step needs a token in a
   subprocess, the step reads the dotenv file and passes the value via
   the `env=` arg, not via "tell the user to source it."
5. **Generate the doc artifact.** A wizard without `WIZARD_FLOWS.md` is
   half-shipped — the doc is the contract with the user.

## Common Mistakes

| Mistake                                                                   | Fix                                                                                                |
| ------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| Writing `wizard.py` before the survey                                     | Stop. Fill out `reference/repo-survey.md`. The step boundaries fall out of the survey.             |
| Step's check function is "did the file get written"                       | Validate the *contents* — run the tool with the captured credential, confirm a 2xx response.       |
| "Tell the user to source the .env file"                                   | Use env injection instead. Read the dotenv values via `config.read_dotenv` and pass to subprocess. |
| Skipping the picker, doing a linear flow                                  | Always offer a picker. The default `recommended` set should be the 80% path.                       |
| Long subprocess (>5s) with no output                                      | Wrap it with `prompts.progress_watch("description")`. Drop it for interactive prompts (interleaves). |
| Forgetting to add `import readline` to `prompts.py`                       | Already in the scaffold. Don't remove it. It enables arrow-key history for `input()`.              |
| Making `WIZARD_FLOWS.md` an afterthought                                  | Generate it in the same PR as the wizard. Every step missing from the doc will get re-asked later. |

## Worked Examples

| Repo                                                       | Notes                                                                                                  |
| ---------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| [`examples/box-java-sdk/`](./examples/box-java-sdk/)       | Java/Gradle preflight + 4-mode auth picker (Developer Token / JWT / CCG / OAuth) + smoke-test snippet. Draft PR upstream: [box/box-java-sdk#1878](https://github.com/box/box-java-sdk/pull/1878). |

The `box-java-sdk` example exercises every reusable primitive in the
scaffold except `progress_watch` (no long-running subprocess in this
flow). Read it end-to-end before applying the scaffold to a new repo —
it's the fastest way to internalize the per-repo customization shape.

When you produce a new wizard, drop a copy of the customized files (just
`setup/` + `scripts/` + the docs artifact) into `examples/<repo-name>/`
in this repo. That builds a real reference library over time.
