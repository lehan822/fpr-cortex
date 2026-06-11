#!/bin/bash
# FPR Cortex Skills — Quick Install
# Usage: curl -sL https://raw.githubusercontent.com/lehan822/fpr-cortex/main/install.sh | bash

set -e

SKILLS_DIR="${HOME}/.agents/skills"
REPO_URL="https://raw.githubusercontent.com/lehan822/fpr-cortex/main"

echo "📦 Installing FPR Cortex skills..."

# Skill name → repo path mapping
declare -A SKILLS=(
  ["fpr-shared"]="skills/shared/auth"
  ["fpr-skill-maker"]="skills/shared/skill-maker"
  ["fpr-pricing"]="skills/domain/pricing"
  ["fpr-supply"]="skills/domain/supply"
  ["fpr-demand"]="skills/domain/demand"
  ["fpr-config"]="skills/domain/config"
)

for skill in "${!SKILLS[@]}"; do
  src="${SKILLS[$skill]}"
  dest="${SKILLS_DIR}/${skill}"
  
  echo "  → ${skill}"
  mkdir -p "${dest}"
  curl -sf "${REPO_URL}/${src}/SKILL.md" -o "${dest}/SKILL.md"
  
  # Also fetch references/ if they exist
  refs_dir="${dest}/references"
  mkdir -p "${refs_dir}" 2>/dev/null || true
  # Try common reference files (silent fail if not exist)
  for ref in pkce-login.md gateway-protocol.md; do
    curl -sf "${REPO_URL}/${src}/references/${ref}" -o "${refs_dir}/${ref}" 2>/dev/null || rm -f "${refs_dir}/${ref}"
  done
  # Clean empty refs dir
  rmdir "${refs_dir}" 2>/dev/null || true
done

echo ""
echo "✅ Done! ${#SKILLS[@]} skills installed to ${SKILLS_DIR}"
echo ""
echo "Next: open Copilot CLI or Claude Code and ask a question like:"
echo '  "查一下 THB budget balance"'
echo ""
echo "First use will open browser for Traveloka SSO login."
