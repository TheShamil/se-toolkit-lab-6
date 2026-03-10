# Review: `lab/tasks/required/task-1.md`

- **Date:** 2026-03-10
- **Convention files used:**
  - `contributing/conventions/writing/tasks.md` — task structure, design principles, conceptual review dimensions (D1–D12)
  - `contributing/conventions/writing/common.md` — writing conventions (4.1–4.26)

---

## Conceptual findings

### D1. Learning objective clarity

No issues found.

### D2. Step-by-step completeness

1. ~~**[Medium]** Line 250: "Start the `Qwen code` coding agent in the terminal inside the project directory" provides no link or reference to setup/installation instructions for the tool. A student unfamiliar with `Qwen code` would not know what command to run or how to launch it.
   **Suggested fix:** Add a link to a wiki page explaining how to install and start the agent (e.g., `[Start the \`Qwen code\` coding agent](../../../wiki/qwen-code.md#start-the-agent)`), or inline the startup command.~~

2. ~~**[Low]** Lines 336, 340, 344: Steps say "try `GET /items/`", "Try `GET /learners/`", "Try `GET /interactions/`" using the vague verb "try", unlike [step 1.4.3](lab/tasks/required/task-1.md#143-run-and-test-locally) (line 291) which uses explicit Swagger UI instructions ("expand ..., click `Try it out`, then `Execute`").
   **Suggested fix:** Use consistent phrasing such as "expand `GET /items/`, click `Try it out`, then `Execute`", or reference the interaction pattern established in step 1.4.3.~~

### D3. Student navigation

No issues found.

### D4. Checkpoints and feedback loops

1. **[Low]** Line 416: [Step 1.4.7](lab/tasks/required/task-1.md#147-update-and-test-on-the-vm) checkpoint says "You should get `200` with `new_records` and `total_records`" but does not show an expected JSON response body, unlike [step 1.4.3](lab/tasks/required/task-1.md#143-run-and-test-locally) (lines 293–300) and [step 1.4.5](lab/tasks/required/task-1.md#145-test-idempotency-locally) (lines 356–361) which include exact expected JSON.
   **Suggested fix:** Add an expected JSON response block for consistency with other checkpoints.

### D5. Acceptance criteria alignment

No issues found.

### D6. Difficulty and progression

No issues found.

### D7. Practical usability

1. ~~**[Medium]** Line 250: No setup instructions or wiki link for the `Qwen code` coding agent. Students who haven't installed or configured the tool would be blocked without external help. (Same root cause as D2 finding #1, manifesting as a usability gap.)
   **Suggested fix:** Add a prerequisite link or reference to a wiki page with installation and launch instructions.~~

### D8. LLM-independence

1. ~~**[Medium]** Lines 250–273 ([step 1.4.2](lab/tasks/required/task-1.md#142-implement-the-pipeline)): The implementation step relies entirely on an AI coding agent. The task does not explicitly state that AI is required for this step, nor does it provide an alternative path (placeholder templates, step-by-step coding instructions) for students who choose not to use AI. Convention 4.16 requires tasks to be completable without LLMs unless AI use is explicitly stated.
   **Suggested fix:** Either (a) add placeholder code or step-by-step implementation guidance as a non-AI path, or (b) explicitly state that this step requires AI and label it as an AI-required part per convention 4.16.~~

### D9. Git workflow coherence

No issues found.

### D10. Conceptual gaps and misconceptions

No issues found.

### D11. Controlled AI steps

1. **[Low]** Lines 252–253: The prompt includes subjective phrasing ("explain each function step by step as if teaching a junior engineer") that may produce variable outputs across AI tools. The review checklist (lines 257–265) partially constrains the result but is a post-hoc review, not a concrete verifiable checkpoint.
   **Suggested fix:** Add a concrete checkpoint at the end of step 1.4.2 (e.g., "The implementation must pass `POST /pipeline/sync` — proceed to step 1.4.3 to verify"), which the task already provides implicitly but could state explicitly to close the feedback loop.

### D12. Autochecker verifiability

No issues found.

---

## Convention findings

### 4.1. Instructions wording

1. **[Low]** Line 291: Three actions chained in one instruction: "expand `POST /pipeline/sync`, click `Try it out`, then `Execute`." Convention 4.1 requires splitting compound instructions into separate numbered steps. Borderline case since these actions form a single Swagger UI interaction flow.
   **Suggested fix:** Split into sub-steps, or keep as-is if considered a single logical action.

### 4.2. Terminal commands

1. ~~**[Medium]** Lines 391–401: Git commands (`cd`, `git fetch`, `git checkout`, `git pull`) and `docker compose up --build -d` are combined in a single terminal block under one "To pull your branch and restart the services on your VM" intention. Convention (tasks.md Section 3, line 194) explicitly states: "`git pull` (version control) and `docker compose up` (container management) must be separate steps even when run in sequence."
   **Suggested fix:** Split into two steps — one for git operations ("To update to your task branch on the VM") and one for Docker ("To rebuild and start the services").~~

### 4.3. Command Palette commands

Not applicable.

### 4.4. Options vs steps

No issues found.

### 4.5. Ordered lists

No issues found.

### 4.6. Mini-ToC

No issues found.

### 4.7. Table of contents

No issues found.

### 4.8. Links and cross-references

No issues found.

### 4.9. Notes, tips, warnings

No issues found.

### 4.10. Images

Not applicable.

### 4.11. Collapsible hints and solutions

No issues found.

### 4.12. Commit message format

No issues found.

### 4.13. Diagrams

No issues found.

### 4.14. `<!-- TODO -->` comments

Not applicable.

### 4.15. `<!-- no toc -->` comments

No issues found.

### 4.16. Code snippets in explanations

Not applicable.

### 4.17. Heading levels in section titles

Not applicable.

### 4.18. Inline formatting of technical terms

1. ~~**[Medium]** Line 13: "Autochecker API" — `Autochecker` is a tool name and must be backticked: `` `Autochecker` API ``.~~
2. ~~**[Medium]** Line 116: "the Autochecker API" — same issue: `` the `Autochecker` API ``.~~
3. ~~**[Medium]** Line 132: "Autochecker bot" — same issue: `` `Autochecker` bot ``.~~
4. ~~**[Low]** Line 302: "the Autochecker" — same issue: `` the `Autochecker` ``.~~
5. ~~**[Low]** Line 322: Inside `<h4>` tag, "Autochecker" should use `<code>Autochecker</code>` (backticks don't render inside HTML tags).~~
6. ~~**[Medium]** Line 328: "autochecker" is both lowercase and unformatted inside `<h4>` tag. Should be `<code>Autochecker</code>` with correct capitalization.~~

### 4.19. Steps with sub-steps

No issues found.

### 4.20. Placeholders in docs

No issues found.

### 4.21. `docker compose up` commands

No issues found.

### 4.22. Environment variable references

No issues found.

### 4.23. Horizontal rules

No issues found.

### 4.24. Inline paths

No issues found.

### 4.25. Branch-on-remote references

Not applicable.

### 4.26. Example IP address

Not applicable.

### Section 1. Task document template (tasks.md)

1. **[Low]** Lines 94–107: [Section 1.2 "Create a `Lab Task` issue"](lab/tasks/required/task-1.md#12-create-a-lab-task-issue) includes branch creation instructions and a naming explanation. The template (tasks.md lines 89–91) specifies that step 1.2 should contain only the issue title. Branch creation belongs in a dedicated step or is covered by the git workflow reference in step 1.1.
   **Suggested fix:** Move branch creation to a separate step (e.g., 1.3) or to the git workflow wiki.

### Recovery guidance (tasks.md 4.19)

1. ~~**[High]** Line 326: Duplicate empty `<h4>500 Internal Server Error</h4>` heading inside the troubleshooting block. This heading has no content — it is immediately followed by `<h4>Connection refused to the autochecker API</h4>` on line 328. Appears to be an editing artifact.
   **Suggested fix:** Remove the duplicate empty `<h4>500 Internal Server Error</h4>` on line 326.~~

---

## TODOs

No TODOs found.

---

## Empty sections

1. ~~Line 326: `<h4>500 Internal Server Error</h4>` — empty heading inside the troubleshooting block (immediately followed by `<h4>Connection refused to the autochecker API</h4>` with no content in between).~~

---

## Summary

| Category | Count |
| --- | --- |
| Conceptual [High] | 0 |
| Conceptual [Medium] | 0 |
| Conceptual [Low] | 2 |
| Convention [High] | 0 |
| Convention [Medium] | 0 |
| Convention [Low] | 2 |
| TODOs | 0 |
| Empty sections | 0 |
| **Total** | **4** |

**Overall:** The remaining issues are conceptual (author decisions required) plus two low-severity convention findings. Step 1.2 includes branch creation instructions that the template reserves for a dedicated step (Section 1 finding), and one borderline compound instruction in step 1.4.3 could optionally be split (4.1 finding). All high and medium violations have been fixed. The D2 "try" verb inconsistency was resolved by referencing the interaction pattern from step 1.4.3.
