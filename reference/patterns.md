# The seven design principles

These distill what makes a setup wizard feel good versus bureaucratic.
Skim this whole doc before customizing the scaffold.

---

## 1. Self-contained

> **Rule:** Cloning the repo is the only prerequisite. The wizard
> handles everything else.

The most common bad wizard pattern: "first source `pat.env`, then run
`init`." That's a tax on every contributor every time they open a fresh
shell. Worse, when they forget, the next command 401s and they think the
wizard is broken.

**Instead:** the wizard reads the dotenv file itself and passes the
values into the subprocess via `env=`. The user never has to source
anything to *get the wizard working*. Sourcing is for ongoing day-to-day
use — that advice goes in the post-completion footer, not in the middle
of an active step.

```python
def step_jira_init() -> bool:
    pat_values = config.read_dotenv(PAT_ENV_FILE)
    token = os.environ.get("JIRA_API_TOKEN") or pat_values.get("JIRA_API_TOKEN")
    if not token:
        print("[FAIL] JIRA_API_TOKEN not set anywhere — run the pat.env step first.")
        return True

    env = os.environ.copy()
    env["JIRA_API_TOKEN"] = token
    env["JIRA_AUTH_TYPE"] = "bearer"
    return _run_interactive(["jira", "init"], env=env) == 0
```

---

## 2. Idempotent

> **Rule:** Re-running is always safe. Every step skips work that's
> already done.

A user re-runs the wizard for three reasons: they want to repair one
broken step, they want to onboard a teammate by walking through the
flow themselves, or something failed mid-run and they're picking up
where it stopped. None of those cases tolerate destructive re-execution.

The shape that makes idempotence cheap:

1. Run the doctor check at the top of the step.
2. If `OK`, return immediately.
3. If `WARN`/`FAIL`, do the repair.

```python
def step_install_jira_cli() -> bool:
    results = checks.check_jira_cli_installed()
    print_results(results, show_ok=True)
    if all(r.severity == "ok" for r in results):
        return True

    if shutil.which("brew"):
        if yes_no("Install via `brew install jira-cli`?", default=True):
            _run_interactive(["brew", "install", "jira-cli"])
    return shutil.which("jira") is not None
```

The check function never prompts. Steps prompt; checks just observe.
That separation is what lets the doctor reuse them as a re-runnable
audit.

---

## 3. Paced output

> **Rule:** Text appears at human reading speed. Tunable via
> `WIZARD_PACE_MS` env var. Falls back to instant output in non-TTY
> contexts.

Walls of text instantly painted to the screen are unreadable. The
wizard's `paced_print(text, pause_ms=N)` writes a section, then sleeps
N milliseconds before continuing — turning "did the user actually read
that warning about API quotas?" into "yes, because they had a
half-second to."

Make pacing optional and tunable:

- `WIZARD_PACE_MS=0` → no pacing (CI-friendly, scripted runs).
- `WIZARD_PACE_MS=120` (default) → comfortable read pace.
- `WIZARD_PACE_MS=400` → slow ramp for first-time users.
- Detect non-TTY (`sys.stdout.isatty()`) and skip pacing automatically.

For very long blocks the user is meant to read carefully (multi-paragraph
explainers, security warnings) consider line-by-line pacing — sometimes
called the "Star Wars crawl" — by passing `pause_ms` between each
`print()`.

---

## 4. Picker-first

> **Rule:** Users choose what to set up. They are never forced through
> every step.

Linear wizards punish users who only need to repair one thing. A picker
solves this — users see the menu, pick what they want, and the rest of
the run skips cleanly.

The picker grammar:

| Input             | Means                                            |
| ----------------- | ------------------------------------------------ |
| `1,3,5`           | comma-separated indices                          |
| `1-3`             | a range                                          |
| `all`             | every step                                       |
| `recommended`     | every step with the `[R]` flag (the default)     |
| `none`            | exit without doing anything                      |
| (blank)           | fall back to `recommended`                       |

Mark a step as `recommended=True` when 80%+ of users will need it.
First-time onboarding should reach a working environment by picking
`recommended`. Optional integrations (specific CLIs, advanced auth
modes, dev-only tools) live behind explicit selection.

---

## 5. Doctor-symmetric

> **Rule:** Every step has a check function. The doctor calls all of
> them, prints results, and exits.

A wizard without a doctor is a black box: when something breaks, users
have no way to ask "is my environment OK now?" Doctor changes that.

The check function is the contract:

```python
def check_jira_cli_installed() -> list[CheckResult]:
    if not shutil.which("jira"):
        return [CheckResult("jira-cli", "warn", "not installed",
                            fix_hint="brew install jira-cli")]
    if not _token_in_env("JIRA_API_TOKEN"):
        return [CheckResult("jira-cli", "warn", "token missing in env",
                            fix_hint="run ./scripts/setup")]
    rc, _, _ = _run(["jira", "me"], timeout=10)
    if rc != 0:
        return [CheckResult("jira-cli", "fail", f"jira me failed (rc={rc})",
                            fix_hint="run `jira init` (see WIZARD_FLOWS.md).")]
    return [CheckResult("jira-cli", "ok", "installed and authenticated")]
```

`severity` is one of `ok`, `warn`, `fail`. The wizard step body and the
doctor both render results via `print_results(results, show_ok=True)`.

---

## 6. Env injection

> **Rule:** When a step needs a token in a subprocess, the step reads
> the dotenv and passes it via the `env=` arg to subprocess.run.

This is the engine of self-containment (principle 1). It deserves its
own section because it's the most common new-wizard mistake.

Wrong (forces the user to source first):

```python
_run_interactive(["jira", "init"])  # jira-cli reads JIRA_API_TOKEN from env
# but the user's shell doesn't have it. 401.
```

Right (wizard reads dotenv, injects):

```python
pat_values = config.read_dotenv(PAT_ENV_FILE)
env = os.environ.copy()
env["JIRA_API_TOKEN"] = pat_values["JIRA_API_TOKEN"]
env["JIRA_AUTH_TYPE"] = "bearer"
_run_interactive(["jira", "init"], env=env)
```

Print a one-liner so the user knows the wizard did this for them:

```
  → injecting JIRA_API_TOKEN from pat.env into the jira init subprocess
```

---

## 7. Progress watchdog

> **Rule:** Long-running commands (>5s) print a "current action" line
> so they don't look hung. Drop the watchdog around interactive prompts
> (it interleaves with the prompt's own output).

Subprocess silence kills user trust faster than failure does. A user
who sees nothing for 30 seconds will Ctrl-C. A user who sees
`current action: installing brew package jfrog-cli` will wait
patiently for several minutes.

The pattern:

```python
with progress_watch("installing jira-cli (brew)"):
    _run_interactive(["brew", "install", "jira-cli"])
```

`progress_watch` spawns a daemon thread that prints the current-action
line if the wrapped block runs longer than 5 seconds, and prints a
`→ done in 47s` suffix when control returns.

**Don't wrap interactive-prompt commands.** `jira init`, `confluence-cli
init`, `gh auth login` all print their own ongoing prompts. The watcher
line interleaves on top of an active prompt and confuses the user.
Keep the watchdog on silent installs (`brew`, `npm install -g`, `uv
sync`), browser-based OAuth (`gcloud auth login`, `box login`), and
file downloads.

---

## Bonus: what the scaffold does so you don't have to

| Convenience                    | Where                                                 |
| ------------------------------ | ----------------------------------------------------- |
| Arrow-key + history in `input()` | `import readline` at top of `prompts.py`            |
| Atomic dotenv writes (no half-written secrets file) | `config.atomic_write_text` |
| Owner-only chmod for secret files | `config.chmod_owner_only`                          |
| Standard glyphs `[OK]`/`[WARN]`/`[FAIL]` | `prompts._GLYPH`                              |
| Banner rendering                | `prompts.banner("Title")`                            |
| Step header rendering           | `prompts.step(n, total, "label")`                    |

Lean on these. Don't reimplement.
