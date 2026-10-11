# Mac/Codex toolkit

An optional setup for Codex on macOS: command-line tools, concise agent guidance, and two reusable skills. It does not install Codex, Homebrew, Node.js, Python, uv, or browser integrations. Install those prerequisites separately as needed.

Requirements: Python 3.10+ and Codex. Homebrew must already be available on PATH to install missing tools. Both Apple Silicon and Intel Homebrew locations are recognized by the doctor; live verification was performed on Apple Silicon.

## What it installs

The installer checks for `git`, `gh`, `rg`, `fd`, `jq`, `yq`, `shellcheck`, and `shfmt`, and installs missing commands with Homebrew. Commands already found on PATH are skipped; their versions are not upgraded or pinned. Installing `yq` uses Homebrew's `yq` formula.

- `mac-tools`: tool and PATH diagnosis, BSD/GNU flag differences, project environments, and a read-only doctor.
- `agent-improvement`: investigate observed workflow failures and apply focused instruction or helper changes. It does not train or change a model.
- `guidance/AGENTS.md`: a managed block in global Codex guidance. Existing text outside the block is preserved.

Review and customize `guidance/AGENTS.md` before applying it. The shipped browser preference is Arc. Skills install under `CODEX_HOME/skills`, normally `~/.codex/skills`. A nonempty `AGENTS.override.md` causes installation to stop so you can resolve its precedence first. Independent existing skills with the same names are not overwritten.

## Preview, apply, and verify

Run from this `mac-codex/` directory:

```sh
python3 scripts/install.py
python3 scripts/install.py --apply
python3 skills/mac-tools/scripts/doctor.py
python3 scripts/verify_codex.py
```

Use `--skip-tools` to install guidance and skills without Homebrew changes. Use `--codex-home /path/to/home` to select an alternative installation directory. The default mode only prints a plan; `--apply` performs changes. Normal Codex filesystem and network permissions still apply when Codex runs the installer.

The installer leaves model settings, `config.toml`, hooks, plugins, permissions, and shell startup files alone. It backs up replaced files under `.local/backups/` before writing. Restart or start a new Codex chat to pick up the guidance and skills, then invoke `$mac-tools` or `$agent-improvement` as needed.

The doctor probes versions and reports paths; missing tools return a nonzero exit status. Node, npm, uv, Codex, and Homebrew are checked but not installed by this toolkit. Use `--json` for structured output. The skill-discovery check uses the local Codex app-server, without creating a chat or requesting a model response; it can report protocol differences with unsupported Codex versions.

Optional skill validation, when Codex's built-in skill-creator validator and uv are available:

```sh
uv run --no-project --with pyyaml scripts/validate_skills.py
```

See the root [OpenCLI guide](../README.md#use-with-codex) to add the upstream browser skills. This toolkit does not install them automatically.

## Restore

The apply command prints a backup manifest path. Keep the checkout and its private `.local/backups/` files if you want to restore later:

```sh
python3 scripts/install.py --restore /absolute/path/to/manifest.json
```

Restore checks every installed file before modifying any. It stops if a file has changed since installation, preserves original file bytes and modes, and leaves Homebrew packages installed. It accepts manifests only from this checkout's backup directory.

## Test without changing your Mac

```sh
python3 -m unittest discover -s tests -v
```

The tests use temporary directories and `--skip-tools`. They check dry run, repeat application, preservation of unrelated guidance and files, restoration of bytes and modes, edited-file protection, existing independent skills, override guidance, and symlink rejection. They do not install packages or write to your real Codex home.

This toolkit is licensed under the repository's [Apache-2.0 license](../LICENSE).

Official guidance: [AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md), [Codex skills](https://learn.chatgpt.com/docs/build-skills). Tool sources: [Homebrew](https://brew.sh), [fd](https://formulae.brew.sh/formula/fd), [yq](https://formulae.brew.sh/formula/yq), [ShellCheck](https://formulae.brew.sh/formula/shellcheck), [shfmt](https://formulae.brew.sh/formula/shfmt).
