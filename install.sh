#!/bin/sh
# FPR Cortex Skills — Quick Install / Update
# Usage: curl -sL https://raw.githubusercontent.com/lehan822/fpr-cortex/main/install.sh | sh

set -e

SKILLS_DIR="${HOME}/.agents/skills"
VERSION_FILE="${HOME}/.agents/skills/.fpr-cortex-version"
REPO_URL="https://raw.githubusercontent.com/lehan822/fpr-cortex/main"

# Fetch latest VERSION
REMOTE_VERSION=$(curl -sf "${REPO_URL}/VERSION" 2>/dev/null || echo "unknown")

# Auto-link fpr-* skills to a known agent skill directory
link_skills() {
  agent_skills_dir="$1"
  mkdir -p "${agent_skills_dir}"
  for skill_path in "${SKILLS_DIR}"/fpr-*/; do
    [ -d "${skill_path}" ] || continue
    name=$(basename "${skill_path}")
    dest="${agent_skills_dir}/${name}"
    rm -f "${dest}"
    ln -sf "${skill_path}" "${dest}"
  done
  echo "   Linked to ${agent_skills_dir}"
}

do_link() {
  echo ""
  echo "🔗 Linking skills to agent directories..."
  [ -d "${HOME}/.claude" ]   && link_skills "${HOME}/.claude/skills"
  [ -d "${HOME}/.opencode" ] && link_skills "${HOME}/.opencode/skills"
  [ -d "${HOME}/.codex" ]    && link_skills "${HOME}/.codex/skills"
}

# Check if already installed and up-to-date
if [ -f "${VERSION_FILE}" ]; then
  LOCAL_VERSION=$(cat "${VERSION_FILE}")
  if [ "${LOCAL_VERSION}" = "${REMOTE_VERSION}" ]; then
    echo "✅ FPR Cortex skills already up-to-date (v${LOCAL_VERSION})"
    echo "   Reinstall: curl -sL ${REPO_URL}/install.sh | sh -s -- --force"
    do_link
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

install_auth_helper() {
  auth_dir="${HOME}/.fpr"
  auth_script="${auth_dir}/fpr-auth.py"
  auth_ref="${SKILLS_DIR}/fpr-tool-shared/references/auth.md"

  echo "  → fpr-auth.py"
  mkdir -p "${auth_dir}"

  awk '
    /^## Script$/ { in_script_section = 1 }
    in_script_section && /^```python$/ { in_code = 1; next }
    in_code && /^```$/ { exit }
    in_code { print }
  ' "${auth_ref}" > "${auth_script}"

  chmod +x "${auth_script}"
}

# Shared skills
install_skill "fpr-tool-shared"   "skills/shared/fpr-tool-shared"   auth.md gateway-protocol.md error-classification.md
install_auth_helper

# FPR tool skills
install_skill "fpr-tool-pricing"   "skills/fpr-tools/fpr-tool-pricing"   autopilot-operations.md budget-operations.md commission-operations.md parameter-standards.md
install_skill "fpr-tool-supply"    "skills/fpr-tools/fpr-tool-supply"    fare-check-workflow.md inventory-staleness.md provider-operations.md parameter-standards.md
install_skill "fpr-tool-demand"    "skills/fpr-tools/fpr-tool-demand"    booking-operations.md parameter-standards.md
install_skill "fpr-tool-sysinteg"  "skills/fpr-tools/fpr-tool-sysinteg"  parameter-standards.md
install_skill "fpr-tool-3ps-data"  "skills/fpr-tools/fpr-tool-3ps-data"  parameter-standards.md

# Save version
echo "${REMOTE_VERSION}" > "${VERSION_FILE}"

echo ""
echo "✅ Done! 6 skills installed to ${SKILLS_DIR} (v${REMOTE_VERSION})"

do_link

echo ""
echo "Next: open Copilot CLI or Claude Code and ask a question like:"
echo '  "查一下 THB budget balance"'
echo ""
echo "First use will open browser for Traveloka SSO login."
echo ""
echo "Update: curl -sL ${REPO_URL}/install.sh | sh"
