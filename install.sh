#!/bin/sh
# FPR Cortex Skills — Quick Install / Update
# Usage: curl -sL https://raw.githubusercontent.com/lehan822/fpr-cortex/main/install.sh | sh

set -e

SKILLS_DIR="${HOME}/.agents/skills"
VERSION_FILE="${HOME}/.agents/skills/.fpr-cortex-version"
REPO_URL="https://raw.githubusercontent.com/lehan822/fpr-cortex/main"

# Fetch latest VERSION
REMOTE_VERSION=$(curl -sf "${REPO_URL}/VERSION" 2>/dev/null || echo "unknown")

# Check if already installed and up-to-date
if [ -f "${VERSION_FILE}" ]; then
  LOCAL_VERSION=$(cat "${VERSION_FILE}")
  if [ "${LOCAL_VERSION}" = "${REMOTE_VERSION}" ]; then
    echo "✅ FPR Cortex skills already up-to-date (v${LOCAL_VERSION})"
    echo "   Reinstall: curl -sL ${REPO_URL}/install.sh | sh -s -- --force"
    exit 0
  fi
  echo "📦 Updating FPR Cortex skills: v${LOCAL_VERSION} → v${REMOTE_VERSION}"
else
  echo "📦 Installing FPR Cortex skills (v${REMOTE_VERSION})..."
fi

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

# Shared skills
install_skill "fpr-shared"      "skills/shared/gateway"     auth.md gateway-protocol.md error-classification.md
install_skill "fpr-skill-maker" "skills/shared/skill-maker" template.md validation-rules.md

# Domain skills
install_skill "fpr-pricing"     "skills/domain/pricing"     autopilot-operations.md budget-operations.md commission-operations.md parameter-standards.md
install_skill "fpr-supply"      "skills/domain/supply"      parameter-standards.md
install_skill "fpr-demand"      "skills/domain/demand"      booking-operations.md parameter-standards.md
install_skill "fpr-sysinteg"    "skills/domain/sysinteg"    parameter-standards.md
install_skill "fpr-3ps-datainfo" "skills/domain/3ps-datainfo" parameter-standards.md

# Save version
echo "${REMOTE_VERSION}" > "${VERSION_FILE}"

echo ""
echo "✅ Done! 7 skills installed to ${SKILLS_DIR} (v${REMOTE_VERSION})"
echo ""
echo "Next: open Copilot CLI or Claude Code and ask a question like:"
echo '  "查一下 THB budget balance"'
echo ""
echo "First use will open browser for Traveloka SSO login."
echo ""
echo "Update: curl -sL ${REPO_URL}/install.sh | sh"
