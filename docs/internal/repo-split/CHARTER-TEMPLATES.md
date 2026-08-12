# Sovereign repo charter templates (HEARTH draft, to instantiate per repo in Phase 2)

# {{REPO_NAME}} Repository Working Notes

## Operating Rules & Identity

This repository (`{{REPO_NAME}}`) is a sovereign, split-out codebase. Its purpose is to {{REPO_PURPOSE}}.

*   **No Cross-Repo Reach-In:** Integration with other repos must occur strictly via published artifacts with verification hashes. **Never** reference files, scripts, or assets using relative paths that reach outside this repository (e.g., `../../../other-repo`).
*   **Checkout Roots:** Scripts must never assume absolute host paths. Derive all locations dynamically from the script context (e.g., `$PSScriptRoot` in PowerShell).
*   **Identity Guard:** Every automation tool or script in this repository must call `tools/Assert-RepoIdentity.ps1` before performing any destructive or state-changing action to ensure it is running in the correct context.

## Landing Work — One Ask, No Relay Race

**"Go" / "push" / "land it" / "ship it" / "good work, merge it in" authorizes the whole remaining chain for that work — commit → push → merge into `main` — in one pass.** Do not stop mid-chain to ask again at each step, and do not park the last step in your closing summary as an offer ("not pushed — say the word").

`main` in this repository is an R&D trunk. Committing straight to it is normal; a feature-branch-and-PR plan is wrong unless explicitly requested.

**Stop and ask only for:** force-push, history rewrite, deleting work you did not create, or anything reaching outside this repo.

**When a hook or rule blocks you, fix the cause and retry — do not hand the failure back.** The blockers you will actually hit:
1. **`main` moves under you.** Background automation or other agents commit here. Pull before you start and again before you push; a rejected push usually just needs `git pull --ff-only`.
2. **Push protection on `origin`.** Realistic-looking credential *fixtures* are rejected. Fix by rewriting the fixture, never by clicking the bypass/allow-this-secret URL.

## Local Verification Loops

Run tests locally and verify builds pass before publishing or pushing:
*   **Test Command:** `{{TEST_COMMAND}}`
*   **Build Command:** `{{BUILD_COMMAND}}`

## Evidence Standard
All significant technical claims or changes must be marked as either:
*   **VERIFIED**: Backed by reproducible output, test runs, or logs using the standard verification gate: `{{TEST_COMMAND}}`.
*   **UNVERIFIED**: Under active research, untested, or waiting for upstream integration.

---TEMPLATE-BOUNDARY---
# Repository Boundary: {{REPO_NAME}}

## Purpose
This repository isolates and encapsulates the core functionality for {{REPO_PURPOSE}}. It acts as a sovereign codebase, decoupled from the main monorepo, communicating solely through formal contract schemas and verified, versioned artifacts.

## Owns
*   {{OWNS}}
*   Build and release manifests specific to this codebase.
*   Unit and integration test suites for its components.

## Does NOT Own
*   {{DOES_NOT_OWN}}
*   Global deployment orchestrators (owned by the owning repo named per line).
*   Cross-cutting configuration overrides (managed at the environment deployment level).

## Published Artifacts
| Artifact Name | Format | Verification / Versioning Mechanism |
| :--- | :--- | :--- |
| `{{PUBLISHED_ARTIFACTS}}` | | |

## Consumed Artifacts
| Artifact Name | Producing Repo | Pin / Version Locking Mechanism |
| :--- | :--- | :--- |
| `{{CONSUMED_ARTIFACTS}}` | | |

## Boundary Guards

### 1. Identity Verification (`tools/Assert-RepoIdentity.ps1`)
*   **How it fails:** If run inside a different repository directory or if the working root does not contain `{{REPO_NAME}}` markers, this script halts execution with a non-zero exit code.
*   **Action on failure:** Check your shell's current working directory. Ensure you are not targeting retired monorepo checkouts.

### 2. Relative Path Sanitizer Hook
*   **How it fails:** A pre-commit hook scans staged files for parent-directory path traversal sequences (e.g., `../..`) that exit the repository root.
*   **Action on failure:** Replace the file-system reference with a dependency on a published, versioned artifact or an environment-based configuration path.

### 3. Contract Schema Lock
*   **How it fails:** CI or local tests fail if API schemas or contract definitions are altered without a corresponding version bump in the manifest files.
*   **Action on failure:** Follow the API evolution guide to update contract versioning before changing underlying payload structures.
