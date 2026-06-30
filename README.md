# fpr-cortex

Public install mirror for FPR Cortex skills.

## Install

```bash
curl -sL https://raw.githubusercontent.com/lehan822/fpr-cortex/main/install.sh | sh
```

This installs the FPR tool skills to `~/.agents/skills/`, installs the auth helper to `~/.fpr/fpr-auth.py`, then links skills into supported local agent skill directories when present.

Installed skills:

- `fpr-tool-shared`
- `fpr-tool-pricing`
- `fpr-tool-supply`
- `fpr-tool-demand`
- `fpr-tool-sysinteg`
- `fpr-tool-3ps-data`

## Update

```bash
curl -sL https://raw.githubusercontent.com/lehan822/fpr-cortex/main/install.sh | sh
```

Restart Codex, Copilot CLI, or Claude Code after installing or updating skills.
