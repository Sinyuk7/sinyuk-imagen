# 🤖 AGENTS.md — Agent Operating Manual

> Optimized for AI coding agents working with partial context
> Target runtime: Hugging Face Spaces (Gradio, stateless container)

---

## 🟢 0. Quick Commands (MANDATORY ENTRY)

Agents MUST use these commands to validate work:

```
pip install -r requirements.txt
python app.py
pytest -q  (if tests exist)
```

---

## 🟢 1. Mission

You are an AI coding agent.

Goals:

* produce correct, minimal, testable code
* follow structure strictly
* avoid hidden behavior
* ensure compatibility with stateless runtime

---

## 🟢 2. Tech Stack

* Python
* Gradio
* Hugging Face Spaces
* External storage (optional for persistence)

---

## 🟢 3. Project Structure

* Organize by feature (vertical slice)
* Each module must be:

  * self-contained
  * independently testable

Rules:

* `_internal/` = private (no cross-import)
* Max directory depth: 3
* File ≤ 300 LOC
* Function ≤ 50 LOC
* ≤ 2 external dependencies per function

---

## 🟢 4. Code Contracts

* 100% typed (no `any`)
* Explicit imports only (no wildcard imports)
* Types must express business meaning

Example:

```
type VerifiedUser = {
  id: string
  role: "enterprise"
  verified: true
}
```

---

## 🟢 5. Function Contract (REQUIRED)

Every core function MUST include:

```
INTENT:
INPUT:
OUTPUT:
SIDE EFFECT:
FAILURE:
```

---

## 🟢 6. Side Effects

* Separate logic from I/O
* Must be declared explicitly

Example:

```
// SIDE_EFFECT: DB_WRITE | NETWORK | FILE_SYSTEM
```

* Prefer immutable data

---

## 🟢 7. Runtime Constraints (Hugging Face Spaces)

### 7.1 Stateless Execution

* Container is ephemeral and may restart anytime:

  * push
  * idle
  * manual restart

Rules:

* DO NOT rely on global variables
* DO NOT store user state in memory
* Persist important state externally

---

### 7.2 File System

* Local filesystem is NOT persistent
* `/tmp` will be cleared

Rules:

* DO NOT rely on `/tmp` for persistence
* DO NOT return long-lived local file paths
* Use in-memory objects or external storage

---

### 7.3 Persistence

Use one of:

* Hugging Face Dataset
* S3 / GCS / Supabase

---

### 7.4 Path Safety

* No absolute paths (e.g. `/Users/...`)
* Use relative paths
* Ensure files exist in repo
* Linux is case-sensitive

---

### 7.5 Dependencies

* All dependencies must be in requirements.txt
* Prefer pinned versions

System dependencies (if needed):

* use packages.txt (e.g. ffmpeg, libgl1)

---

### 7.6 Secrets & Network

* Use environment variables (Secrets)
* Never hardcode API keys

Must handle:

* timeouts
* API failures
* retries when safe

---

## 🟢 8. Gradio Rules

### File Outputs

* Do NOT return unstable `/tmp` paths
* Return objects or verified files

### Concurrency

* No shared mutable globals
* Avoid race conditions
* Use queue if needed

### UI State

* Must be refresh-safe OR disposable
* Use gr.State or external storage if needed

---

## 🟢 9. Models & Large Files

* Do NOT store models in repo
* Load from Hugging Face Hub
* Use caching

---

## 🟢 10. Boundaries (CRITICAL)

### ALWAYS

* keep functions small and deterministic
* log important steps
* handle errors explicitly

### ASK BEFORE

* modifying multiple files
* changing architecture
* adding new dependencies

### NEVER

* hardcode secrets
* rely on hidden state
* silently ignore errors
* return null instead of errors
* persist data locally

---

## 🟢 11. Observability

* Structured logs preferred (JSON)
* All errors must be:

  * caught
  * logged
  * surfaced

---

## 🟢 12. Deployment Checklist

Before finishing, verify:

* app runs from cold start
* no `/tmp` persistence
* no global state dependency
* dependencies complete
* secrets via environment
* concurrency-safe
* logs available

---

## 🟢 13. Philosophy

* Explicit > implicit
* Simple > clever
* Deterministic > magical
* Stateless > stateful
