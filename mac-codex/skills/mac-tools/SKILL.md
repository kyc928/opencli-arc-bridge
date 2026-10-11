---
name: mac-tools
description: Diagnose, select, install, and use command-line tools on macOS when a task depends on local tool availability, shell behavior, or a failing Mac command.
---

# Mac Tools

Use the tools already exposed in the session. For service or app work, prefer a purpose-built connector or CLI when it supports the requested operation. For actual UI work, use the available Computer Use APIs and the relevant browser skill; do not substitute guessed UI state or shell-driven clicks.

## Diagnose before changing setup

Run `python3 <skill-directory>/scripts/doctor.py` for a baseline tool check, or add `--json` for structured output. It reports executable paths and versions, including tools found outside the current PATH. It does not install tools, inspect chats, or print environment variables. A nonzero exit means a baseline tool is unavailable in the current PATH or a version probe failed; inspect the status before recommending a fix.

For a task-specific failure, check the exact executable and its supported flags. macOS ships BSD tools; GNU examples may require different options (`sed -i`, `date`, `stat`, and `readlink` commonly differ). Prefer portable flags or an already installed GNU executable such as `gdate` when needed. Do not replace system binaries or add global aliases to make one command work.

Apple Silicon Homebrew commonly lives under `/opt/homebrew`; Intel or Rosetta installations may use `/usr/local`. Verify the machine architecture and resolved executable rather than assuming either path. An executable outside the current PATH is a discovery issue, not proof that installation is needed. A login shell, interactive terminal, and GUI-launched Codex can inherit different PATH values. Diagnose the failing context, use an explicit executable path when sufficient, and make persistent shell or app environment changes only within the requested setup scope.

Distinguish `command not found`, unsupported flags, filesystem denial, network/DNS failure, missing credentials, and macOS privacy permission denial. Preserve the exact error needed to identify the cause without dumping environment values, tokens, or unrelated logs. Follow the session's escalation flow for sandbox denials; use macOS permission controls for a demonstrated privacy denial. Do not relabel a network restriction as an installation failure.

## Select and install only what the task needs

Use the existing package manager and check current official package or tool documentation when choosing a package or unfamiliar options. Avoid a bulk upgrade or reinstall as a repair strategy. Before a package mutation, respect the user's scope and the active execution permissions; a tool diagnosis alone does not authorize installation.

For Python work, use an existing project virtual environment or `uv` environment. Use `uv tool` for a standalone Python CLI when appropriate. Keep packages out of system Python and avoid `sudo pip` or bypassing externally managed environment protections.

Use ShellCheck and shfmt for supported Bash/sh scripts. They do not validate zsh; use `zsh -n` for zsh syntax and verify behavior with a scoped run when useful. After a setup change, rerun the failed command or the relevant doctor checks and report the concrete result.
