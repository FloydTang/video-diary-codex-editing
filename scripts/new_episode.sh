#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: bash scripts/new_episode.sh EP01 标题"
  exit 1
fi

episode="$1"
shift
title="$*"

safe_title="${title// /_}"
dir="episodes/${episode}_${safe_title}"

if [[ -e "$dir" ]]; then
  echo "Episode already exists: $dir"
  exit 1
fi

mkdir -p "$dir/raw" "$dir/assets" "$dir/project" "$dir/renders" "$dir/qa" "$dir/srt_work"
cp templates/episode/README.md "$dir/README.md"
cp templates/episode/口播稿.md "$dir/口播稿.md"
cp templates/episode/素材清单.md "$dir/素材清单.md"
cp templates/episode/剪辑规划.md "$dir/剪辑规划.md"
touch "$dir/raw/.gitkeep" "$dir/assets/.gitkeep"

echo "Created $dir"
echo
echo "Next:"
echo "1. Put raw talking-head video and SRT into $dir/raw"
echo "2. Put screenshots/recordings/images into $dir/assets"
echo "3. Ask Codex to follow AGENTS.md and edit this episode"

