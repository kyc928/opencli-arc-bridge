---
name: agent-improvement
description: Audit and improve Codex workflows when the user requests an effectiveness audit, identifies recurring failures, supplies a correction, or asks for a lasting workflow improvement. Use observed evidence to make a scoped instruction, skill, or helper-script fix.
---

# Agent Improvement

Start from the requested outcome and evidence available in this conversation, the affected files, or the specific logs or chats the user has identified. Describe the behavior that failed and its practical consequence. A correction is evidence about that case; determine whether it is a stable preference or a task-specific instruction before persisting it.

Inspect the relevant AGENTS.md, skill, or helper before changing it. Preserve existing preferences and useful constraints. Trace the failure to a concrete cause such as missing context, an ambiguous trigger, an incorrect command, an unnecessary approval stop, or an unchecked result. If the cause remains uncertain, name the uncertainty and use a focused check; do not invent a recurring pattern from one example.

Apply the smallest useful fix within existing authorization:

- Put repository-specific guidance in that repository's AGENTS.md.
- Put a reusable task workflow in the relevant skill, with a precise trigger and only the details that change decisions.
- Put repeated, deterministic mechanics in a small helper script when it reduces a demonstrated source of errors.

Use user-wide instructions only for a confirmed preference that applies across projects. If the needed mutation is outside the authorized scope, prepare a concrete diff or staged file so the final approval has a reviewable result. Do not expand a targeted correction into a broad rewrite, a blanket rule for unrelated tasks, or a new installation.

Verify the fix against the observed failure or a small realistic example. Validate skill frontmatter with the available skill validator and run changed helper scripts when appropriate. Report what changed, what evidence justified it, and what the verification shows. Instruction and tool changes can improve future behavior; do not claim that they train or modify the underlying model.

Keep this work tied to the user's request. Do not sweep unrelated chats, collect private history, or create recurring automations as part of an audit. A requested recurring follow-up uses the app's automation tools with its own scope and notification intent.
