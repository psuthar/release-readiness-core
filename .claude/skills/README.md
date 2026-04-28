# Claude skills (release-readiness-core)

Skills are procedural contracts in **`SKILL.md`** files under this directory. Agents should **read and follow** the relevant skill when the user’s task matches.

| Skill | When to use |
|-------|-------------|
| **`epic-run/`** | User says **`run epic SCRUM-XX`**, **`continue epic SCRUM-XX`**, or **`continue epic run for SCRUM-XX`**. Executes all epic children with **FULL_AUTO** using PR Gate success + mergeability rules; **`continue`** must **drain all remaining Jira work**, not a single ticket. If you **squash-merge yourself** after a halt, **`continue epic`** reconciles **Jira Done**, **`main`**, and **branch cleanup**—see `epic-run/SKILL.md` (**User override**). |
| **`jira-work-decomposition/`** | User says **`decompose <initiative>`** or asks how to break work into tickets. Run this **before** ticket writing to produce a sequenced, typed ticket list. |
| **`jira-ticket-authoring/`** | User says **`write jira ticket`**, **`draft epic/story/task/bug`**. Run this **after** decomposition to produce paste-ready, consistently structured Jira tickets. |
| **`feature-plan/`** | User asks for a **plan** before implementation (no code yet). |
| **`repo-map/`** | Orientation and repository layout. |
| **`smoke-tests/`** | Authoring or extending smoke/integration checks for package behavior. |
| **`e2e-tests/`** | Authoring or extending end-to-end style scenario tests (CLI/report flows). |

**Epic vs `CLAUDE.md` §8:** Standalone **`implement SCRUM-XX FULL_AUTO`** and epic runs both require PR Gate success + `mergeable_state: clean`; epic adds sequencing/resume rules. See **`CLAUDE.md` §10** and **`epic-run/SKILL.md`**.

**No separate `skills.md` at repo root** — this file is the index.
