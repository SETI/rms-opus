# Executor guide — `rewrite` branch

This branch is a multi-PR modernization of rms-opus, executed one PR at a time by an
AI sub-agent with a fresh context per PR. **The complete, binding specification is
`plans/2026-07-18_opus_modernization_plan.md`.** If you are executing a PR:

1. Read `plans/2026-07-18_opus_modernization_plan.md` §1–§3, the §4 preamble, §4a (execution protocol), your assigned PR's
   section, §5/§5a (CI), §6 (verification), and the Execution notes appendix. That is
   your entire briefing; do not rely on any prior conversation.
2. Execute **only** your assigned PR. Never start the next PR. PRs are strictly
   sequential; your PR builds on the merged result of all earlier ones.
3. Rules that override any other instinct:
   - Both CI workflows must be green on your PR before you are done.
   - Move PRs use strict move/modify commit separation: the move commit contains ONLY
     `git mv` renames; rewrites follow in the next commit(s) of the same PR.
   - Follow the plan's decision tables exactly; they exist so you never make a design
     judgment call.
   - **Stop-and-report:** if reality contradicts the plan (a claim is stale, a step is
     impossible as written, a decision table misses a case), stop and report the
     contradiction in the PR — do not improvise. Mechanical drift (moved line numbers,
     changed counts) that doesn't change an instruction's meaning is not a
     contradiction; note it and proceed.
   - Record any fact later PRs need as a dated bullet in `plans/2026-07-18_opus_modernization_plan.md`'s "Execution notes"
     appendix, amended in your own PR. Never edit the plan body or earlier notes.
4. Before opening the PR, run the **adversarial pre-PR review** (§4a): launch a fresh
   opus-class sub-agent to review the full diff, address its findings, and repeat with a
   new reviewer — up to **four churn-focused passes** (passes 2+ focus on what you changed
   in response to the prior pass) until one comes back clean. If the fourth pass is still
   not clean, **stop-and-report** why the reviews aren't converging instead of opening the
   PR.
5. Definition of done: an open PR against `rewrite` (never merge it yourself), titled with
   its **phase letter + PR number** (e.g. `[Phase A · PR-01] feat: …`), with both
   workflows green, a description covering what/why/testing evidence **and the adversarial
   review summary**, plus any PR-specific artifacts the plan requires (e.g. PR-07's `_meta`
   diff, PR-13's rule-annotated fixture diff, PR-21's content-parity checklist). After
   opening, run the **post-PR CodeRabbit loop** (§4a): respond to every CodeRabbit comment
   — fix the correct ones, reason-reject the rest — wait for it to settle, and re-trigger
   with a `@coderabbitai review` comment in 10-minute increments if it's out of reviews.
   Declare **ready to merge only once CI and CodeRabbit are both stable and green**; hand
   the settled PR to the orchestrator to merge.
6. Conventional-commit titles (`feat:`/`fix:`/`refactor:`/`chore:`/`test:`/`docs:`…);
   one logical change per commit.

Repo facts an executor needs on day one: Python entry points and layout are described in
`plans/2026-07-18_opus_modernization_plan.md` §2; configuration/secrets handling is `plans/2026-07-18_opus_modernization_plan.md` §3 (it changes at PR-08 —
check the Execution notes for where the sequence currently stands); the coding standards
are the `.cursor/rules/*.mdc` files (added in PR-01), with one repo-specific waiver:
public web API backwards compatibility is preserved despite the rules' no-back-compat
policy (see `plans/2026-07-18_opus_modernization_plan.md` §1 decisions table).
