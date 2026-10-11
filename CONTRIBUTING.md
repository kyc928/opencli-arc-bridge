# Contributing

This repository maintains a small compatibility patch against a pinned OpenCLI release. Prefer fixing shared behavior upstream in [jackwener/OpenCLI](https://github.com/jackwener/OpenCLI).

Run `python3 scripts/build.py` before proposing changes. It applies the patch to clean upstream source, runs the extension tests, checks production TypeScript, and creates the extension package. Include regression coverage for changes to startup, ownership, or session recovery.

For bug reports, include your Arc, macOS, OpenCLI CLI, and extension versions, whether `opencli doctor` passes, and whether foreground mode works. Remove account data, cookies, tokens, private URLs, and identifying paths from logs before sharing them.

Do not broaden extension permissions to work around a failure. Update the pinned commit, patch, attribution notices, and verification results together when changing upstream versions.
