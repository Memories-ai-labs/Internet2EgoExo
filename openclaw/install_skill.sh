#!/usr/bin/env bash
set -euo pipefail

SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_SOURCE="${SELF_DIR}/packages/video-searching-openclaw-skill/skills/video-searching"
OPENCLAW_HOME_DIR="${OPENCLAW_HOME:-${HOME}/.openclaw}"
TARGET_SKILLS_DIR="${OPENCLAW_HOME_DIR}/skills"
TARGET_SKILL_DIR="${TARGET_SKILLS_DIR}/video-searching"
MODE="${1:-link}"

if [[ ! -d "${SKILL_SOURCE}" ]]; then
  echo "Skill source not found: ${SKILL_SOURCE}" >&2
  exit 1
fi

mkdir -p "${TARGET_SKILLS_DIR}"
rm -rf "${TARGET_SKILL_DIR}"

if [[ "${MODE}" == "--copy" ]]; then
  cp -R "${SKILL_SOURCE}" "${TARGET_SKILL_DIR}"
  echo "Installed skill by copy to ${TARGET_SKILL_DIR}"
else
  ln -s "${SKILL_SOURCE}" "${TARGET_SKILL_DIR}"
  echo "Installed skill by symlink to ${TARGET_SKILL_DIR}"
fi

cat <<'EOF'
Next steps:
1. Ensure GOOGLE_API_KEY and YOUTUBE_API_KEY are set in OpenClaw global env vars.
2. Ensure git and uv are installed on the OpenClaw host.
3. Enable skills.entries["video-searching"].enabled=true in openclaw.json.
4. Optional: set skills.entries["video-searching"].env.VIDEO_SEARCHING_AGENT_ROOT to override managed bootstrap path.
5. Recommended for Telegram typing reliability:
   - openclaw config set agents.defaults.typingMode '"message"'
   - openclaw config set agents.defaults.typingIntervalSeconds 6
   - openclaw gateway restart
6. Use /video_searching <query> in your messaging channel.
EOF
