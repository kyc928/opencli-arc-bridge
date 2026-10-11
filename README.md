# OpenCLI Arc bridge

A community compatibility build of the [OpenCLI Browser Bridge](https://github.com/jackwener/OpenCLI) for an Arc startup stall. It lets the bridge connect when Arc's `chrome.tabGroups.query()` never resolves.

The CLI and most extension code are upstream OpenCLI. This repository contains a small source patch, regression tests in that patch, a loadable extension, and a reproducible build script. It is not an official OpenCLI or Arc release.

## Optional Mac/Codex setup

The [Mac/Codex toolkit](mac-codex/README.md) provides a dry-run-first installer, a Homebrew tool list, a managed guidance block, and the `mac-tools` and `agent-improvement` skills. It includes backups, restore, a tool doctor, and a Codex skill-discovery check. This toolkit is optional; the Arc extension works independently.

```sh
cd mac-codex
python3 scripts/install.py          # preview
python3 scripts/install.py --apply  # install tools, guidance, and skills
```

Review `mac-codex/guidance/AGENTS.md` first: its browser preference is Arc, and you can edit that line to match your workflow. See the toolkit guide for prerequisites, verification, and restoring prior files.

## Why it exists

On the tested Mac, the official extension installed correctly and could reach the local daemon, but startup waited indefinitely for tab-group recovery. A bounded read-only probe remained pending after three seconds. That prevented the worker's startup gate from completing and left `opencli doctor` reporting no connected extension.

This patch checks tab-group support once. If the API is missing, rejects, or stays pending for 1.5 seconds, the bridge falls back to upstream's existing ungrouped owned-tab path. Only the read-only probe is timed out; group mutations are not raced against timers. Owned windows, tab leases, recovery gates, and transport checks remain intact.

## Install

Requirements: Arc on macOS, and Node.js 20.18.1 or newer for OpenCLI. Node 22 was used for verification.

1. Install the tested CLI version:

   ```sh
   npm install -g @jackwener/opencli@1.8.8
   ```

2. Download and unzip the [latest release](https://github.com/kyc928/opencli-arc-bridge/releases/latest), or clone this repository and use its `extension/` folder.
3. In Arc, open `arc://extensions`, enable **Developer mode**, and disable the official OpenCLI extension if installed.
4. Click **Load unpacked** and select the extracted `extension/` directory containing `manifest.json`.
5. Keep that directory in place. Confirm **OpenCLI — Arc compatibility** is enabled, then run:

   ```sh
   opencli doctor
   opencli profile list
   ```

With one connected profile, OpenCLI selects it automatically. For multiple profiles, use `opencli profile use <contextId-or-alias>`.

### Verify browser operation

Foreground mode worked on the tested Arc installation; the initial default-window attempt returned a blank page.

```sh
opencli browser arc-check open https://example.com --window foreground
opencli browser arc-check state --window foreground
opencli browser arc-check close
```

The state should show Example Domain page contents. Close releases the session's owned tab lease. This compatibility build does not guarantee every upstream adapter or every Arc version works.

### Use with Codex

The bridge works with OpenCLI clients, including Codex's upstream skills. No MCP server configuration is required for the CLI-plus-skills integration. Install the pinned skills using Codex's skill installer, for example:

```sh
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --repo jackwener/OpenCLI \
  --ref 8271afc67e8504bda94c147f446ee29775d08274 \
  --path skills/opencli-usage skills/opencli-browser skills/opencli-autofix \
  skills/opencli-adapter-author skills/opencli-browser-sitemap skills/opencli-sitemap-author
```

Use the installer when those skills are not already installed; existing destinations may be rejected. Then prompt Codex: `$opencli-browser Read this page using Arc with --window foreground.`

## Permissions and updates

The manifest has the same permissions and content security policy as upstream: debugger, tabs, cookies, activeTab, alarms, storage, tabGroups, downloads, and access to all websites. These permissions allow browser automation against logged-in pages. Install only if you trust the code and understand that access.

Unpacked extensions do **not** receive Chrome Web Store updates. Review new releases, replace the extracted folder's files, and click **Reload** in the extension manager. Rerun `opencli doctor` and the browser check afterward. To return to upstream, disable this build, enable the official extension, and verify connectivity. Keep only one bridge enabled per browser profile.

## Build from source

Requires Git, Python 3.10+, Node.js, and npm. The script downloads the pinned upstream source and dependencies using upstream lockfiles, with npm install scripts disabled:

```sh
python3 scripts/build.py
```

It produces `build/extension/`, a release ZIP, `SHA256SUMS`, and provenance metadata. It runs all extension-project tests, checks production TypeScript, and builds with Vite before packaging. The checked-in patch includes both implementation and regression tests.

Upstream base: OpenCLI v1.8.8, commit `8271afc67e8504bda94c147f446ee29775d08274`; extension version 1.0.24. The compatibility label is `1.0.24 + Arc compatibility 1`.

## Verification

- 105 extension tests passed, including missing/rejected/stalled APIs, late completion, startup ordering, and tab ownership.
- Production TypeScript checking and the production build passed.
- The full upstream extension type check has eight errors in unchanged test files, reproduced on pristine release source. The build script checks production code separately.
- On one Apple Silicon Mac with Arc: daemon and extension connectivity passed; a named foreground session opened and read Example Domain, then released its lease.

## Does this already exist?

Checked GitHub repositories, upstream issues/PRs, and upstream main on 2026-10-11 UTC. No equivalent public Arc compatibility repository was found in those searches; this is not a claim that none exists anywhere. Upstream main at `77af6bc433c1818a4abb1c8928e2a7fd0bbae376` still had the same `background.ts` as the pinned release.

Related work:

- [PR #2169: browser tab grouping toggle](https://github.com/jackwener/OpenCLI/pull/2169), open at the time checked. It provides a user preference for grouping and addresses saved-group clutter. This patch handles an unavailable or hanging API automatically during startup.
- [Issue #1777: Arc connectivity abort](https://github.com/jackwener/OpenCLI/issues/1777), closed after transport deadline fixes. Its failure occurred with an already connected extension; the stall observed here prevented connection.
- [Issue #2069: disable group creation](https://github.com/jackwener/OpenCLI/issues/2069), related to the toggle PR.

Prefer an official upstream fix when one covers this startup behavior. See [CONTRIBUTING.md](CONTRIBUTING.md) for maintenance guidance.

## License and attribution

[Apache-2.0](LICENSE). Derived from OpenCLI, Copyright 2025 jackwener. See [NOTICE](NOTICE) for modified-file notices and attribution. This project is not affiliated with OpenCLI or The Browser Company.
