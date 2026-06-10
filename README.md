# setup-wizard-squared

A Cursor skill that helps an AI agent build a setup wizard for any repo —
plus a plug-and-play Python scaffold the agent can drop into a target
codebase and customize.

> *"setup wizard squared"* — a setup wizard for building setup wizards.

## What you get

| Path                                         | Purpose                                                                                                |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| [`SKILL.md`](./SKILL.md)                     | The skill the agent loads. When to use, the survey-first method, and the scaffold map.                 |
| [`reference/patterns.md`](./reference/patterns.md) | The seven design principles that make a setup wizard feel good (paced output, idempotence, etc.). |
| [`reference/repo-survey.md`](./reference/repo-survey.md) | Checklist the agent fills in when inspecting a target repo before writing steps.            |
| [`reference/docs-template.md`](./reference/docs-template.md) | Template for the user-facing wizard docs (Mermaid decision tree included).               |
| [`scaffold/`](./scaffold/)                   | Drop-in Python the agent copies into the target repo and customizes.                                   |
| [`examples/`](./examples/)                   | Worked examples — real repos the scaffold has been applied to.                                         |

## How it works

```mermaid
flowchart LR
    A[User asks for a setup wizard<br/>in repo X] --> B[Agent loads<br/>setup-wizard skill]
    B --> C[Agent surveys repo X<br/>using reference/repo-survey.md]
    C --> D[Agent copies scaffold/<br/>into repo X]
    D --> E[Agent writes<br/>repo-specific step functions]
    E --> F[Agent generates docs<br/>from reference/docs-template.md]
    F --> G[User runs ./setup<br/>in repo X]
```

## The seven design principles

The scaffold and skill encode lessons from a hardened production wizard.
Full discussion in [`reference/patterns.md`](./reference/patterns.md).

1. **Self-contained** — clone repo, run wizard, done. No prep steps.
2. **Idempotent** — re-running is always safe; every step skips work already done.
3. **Paced output** — text appears at human reading speed, tunable via env var.
4. **Picker-first** — users choose what to set up, never forced through every step.
5. **Doctor-symmetric** — every step has a check function the doctor can re-run.
6. **Env injection** — wizard reads tokens itself and feeds them to subprocesses.
7. **Progress watchdog** — long-running commands surface a "current action" line.

## Worked examples

| Repo                          | Wizard scope                                               | Status     |
| ----------------------------- | ---------------------------------------------------------- | ---------- |
| [box/box-java-sdk](./examples/box-java-sdk/) | Java + Gradle preflight, Developer Token / JWT / CCG / OAuth auth picker, smoke-test snippet | Draft PR: [box/box-java-sdk#1878](https://github.com/box/box-java-sdk/pull/1878) |
| [box/box-python-sdk](./examples/box-python-sdk/) | Python + pip preflight (with optional editable install), Developer Token / JWT / CCG / OAuth auth picker, smoke-test snippet | Draft PR: [box/box-python-sdk#1475](https://github.com/box/box-python-sdk/pull/1475) |

Same scaffold, two ecosystems. The Java/Python pair shows the
scaffold is genuinely portable — only step bodies and check
functions change between them.

## License

Apache-2.0. See [`LICENSE`](./LICENSE).
