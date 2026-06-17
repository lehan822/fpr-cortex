#!/bin/sh
# FPR Cortex Skills — Quick Install
# Usage: curl -sL https://raw.githubusercontent.com/lehan822/fpr-cortex/main/install.sh | sh

set -e

SKILLS_DIR="${HOME}/.agents/skills"
REPO_URL="https://raw.githubusercontent.com/lehan822/fpr-cortex/main"

echo "📦 Installing FPR Cortex skills..."

install_skill() {
  name="$1"
  src="$2"
  shift 2
  dest="${SKILLS_DIR}/${name}"

  echo "  → ${name}"
  mkdir -p "${dest}"
  curl -sf "${REPO_URL}/${src}/SKILL.md" -o "${dest}/SKILL.md"

  # Fetch references if any are specified
  if [ $# -gt 0 ]; then
    mkdir -p "${dest}/references"
    for ref in "$@"; do
      curl -sf "${REPO_URL}/${src}/references/${ref}" -o "${dest}/references/${ref}" 2>/dev/null || rm -f "${dest}/references/${ref}"
    done
  fi
  # Clean empty refs dir
  rmdir "${dest}/references" 2>/dev/null || true
}

install_skill "fpr-shared"      "skills/shared/auth"       pkce-login.md gateway-protocol.md
install_skill "fpr-skill-maker" "skills/shared/skill-maker" template.md validation-rules.md
install_skill "fpr-pricing"     "skills/domain/pricing"    budget-operations.md commission-operations.md parameter-standards.md
install_skill "fpr-supply"      "skills/domain/supply"     fare-check-workflow.md provider-operations.md
install_skill "fpr-demand"      "skills/domain/demand"     booking-operations.md search-simulation.md
install_skill "fpr-config"      "skills/domain/config"     feature-flags.md

echo ""
echo "✅ Done! 6 skills installed to ${SKILLS_DIR}"
echo ""
echo "Next: open Copilot CLI or Claude Code and ask a question like:"
echo '  "查一下 THB budget balance"'
echo ""
echo "First use will open browser for Traveloka SSO login."
