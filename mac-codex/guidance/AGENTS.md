## Personal Mac and agent defaults

- Complete authorized tasks through implementation and proportionate verification. Resolve routine choices from the project and available evidence; ask when a missing choice materially affects the result.
- Prefer structured connectors or command-line tools for work they handle well. Use available browser and Computer Use tools for tasks that require the user interface.
- For local browser tasks, prefer Arc unless the user specifies another browser or the task requires a browser-specific tool.
- For Mac tool or PATH problems, use the `mac-tools` skill. macOS commands often use BSD options; select flags for the executable actually in use. Use ShellCheck and shfmt for supported shell dialects, and `zsh -n` for zsh syntax checks.
- Keep Python dependencies in a project environment, using the project's existing dependency manager or uv. Respect the repository's package manager and lockfiles.
- Match verification to the behavior changed. After relevant checks pass, finish with the result, evidence, and any remaining limitation.
- When asked to improve agent behavior or when a recurring failure needs a durable fix, use `agent-improvement`. Prefer a focused project instruction or reusable skill backed by observed evidence; keep personal defaults concise.
