# Repo survey checklist

Fill this in **before** writing any wizard code. The step boundaries fall
out of the survey naturally — guessing at them upfront leads to bundled
steps that break the doctor pattern.

For each section: copy this file into the target repo as
`SETUP_WIZARD_SURVEY.md` (or keep notes in the agent's working memory),
fill in the answers, then iterate.

---

## 1. Repo identity

- **Name:**
- **Primary language:**
- **Build system:** (Maven, Gradle, npm, pip, cargo, go mod, etc.)
- **License:** (matters if you'll fork it)
- **Public or internal?**

## 2. Required system tools

What must already be on PATH for the wizard's first step to do anything?

- [ ] Language runtime (e.g. `java -version`, `node --version`, `python3
      --version`, `go version`)
- [ ] Package manager / build tool (`gradle`, `mvn`, `npm`, `pip`,
      `cargo`, `go`)
- [ ] Source control (`git`, possibly `git-lfs`)
- [ ] Other CLI dependencies the build calls out to (`docker`, `kubectl`,
      cloud SDK, etc.)

For each: how does the README tell users to install it? That's your
fix-hint text.

## 3. Configuration files

What files does the repo expect to find at the root (or in well-known
locations) that contain user-specific values?

| Filename            | Format             | What it stores                            | Created by what step? |
| ------------------- | ------------------ | ----------------------------------------- | --------------------- |
| `.env`              | KEY=VALUE          |                                           |                       |
| `.env.local`        | KEY=VALUE          |                                           |                       |
| `local.properties`  | java properties    |                                           |                       |
| `box-config.json`   | JSON               |                                           |                       |
| `~/.something/cfg`  | tool-specific      |                                           |                       |

If `.env.example` (or equivalent) exists in the repo, dump its keys here.
Each key is a candidate for a wizard prompt.

## 4. Secrets to collect

What sensitive values does the wizard prompt the user for? Each one needs:

| Secret name             | Where to mint it                                  | Format / length hint               | Goes into which file?      |
| ----------------------- | ------------------------------------------------- | ---------------------------------- | -------------------------- |
| e.g. `BOX_DEV_TOKEN`    | https://app.box.com/developers/console            | 64-char alphanumeric, 60-min TTL   | `.box-config.json` (auth.token) |

For each:
- Self-service or admin approval required?
- Expires? How often must it be re-rotated?
- Is the wizard *creating* the secret (e.g. running `gcloud auth login`
  to mint a token) or *capturing* a secret the user already has?

## 5. Auth flows already implemented in the repo source

Read the source for auth code. Most SDKs and tools support multiple
modes; the picker should reflect them.

| Auth mode         | File / class                    | What state does it need?                           |
| ----------------- | ------------------------------- | -------------------------------------------------- |
| Developer Token   |                                 |                                                    |
| OAuth 2.0         |                                 | client ID, secret, redirect URI                    |
| JWT               |                                 | private key, passphrase, JWT config JSON, key ID   |
| Client Credentials |                                |                                                    |
| API key           |                                 |                                                    |

Each implemented mode → one row in the wizard's auth-mode picker.

## 6. Existing onboarding documentation

Quote the relevant sections verbatim — the wizard should mirror this
flow exactly, not invent a new one.

- README "Getting Started":
- README "Authentication":
- CONTRIBUTING.md "Development setup":
- Wiki / external docs:

Common gaps in existing docs (the wizard's chance to add value):
- "Where do I generate the token?"
- "Where do I put the token after I have it?"
- "How do I verify it's working?"
- "What if it doesn't work?"

If those questions don't have crisp one-screen answers in the README,
the wizard fills them.

## 7. Smoke test

What's the simplest thing a successfully-set-up developer can run that
proves their environment works?

For an SDK, this is usually a 3–5 line program that:
1. Loads the configured credentials.
2. Calls the API once (e.g. "fetch current user").
3. Prints something the user can recognize.

For a service, it's typically `./gradlew test` or `npm test` for a
single fast test class.

Write the smoke test as the **last wizard step** (or as a separate
`./scripts/smoke-test`), so the wizard's success criterion is "this
runs to completion."

## 8. Doctor expectations

When a user says "something broke, what's wrong?", what should the
doctor check?

- [ ] Each system tool from §2 is on PATH.
- [ ] Each config file from §3 exists.
- [ ] Each secret from §4 is set somewhere reachable (env var or
      config file).
- [ ] The smoke test from §7 passes (optional — slower; consider behind
      a `--smoke` flag).

Each bullet → one check function in `setup/checks.py`.

## 9. Step boundaries

By the end of the survey you should have a clear answer to:

> **What are the 3–7 steps the wizard will offer?**

Write them out. Mark each as recommended (default-on) or optional. For
each, fill in the row of the table this becomes in `WIZARD_FLOWS.md`:

| Step | Label                | Recommended | Check                  | Repair                | Writes                 |
| ---- | -------------------- | ----------- | ---------------------- | --------------------- | ---------------------- |
| 1    | Java + Gradle preflight | yes      | `java -version`, `./gradlew --version` | print install hints | nothing               |
| 2    | Pick auth mode       | yes         | (none — selection step) | prompt picker        | `.box-auth-mode`       |
| 3    | Developer Token entry | yes (if mode=devtoken) | token env or config | getpass + write to config | `.box-config.json` |
| ...  |                      |             |                        |                       |                        |

When this table is filled in, you're ready to write `wizard.py`.
