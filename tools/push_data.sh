#!/usr/bin/env bash
# 把生成的数据文件推到 main：先存到临时目录，每次尝试都从最新的 main 开始、放回文件、提交、推送。
# 别的工作流同时推送时不会因为 rebase 冲突而悄悄失败。用法：bash tools/push_data.sh "<提交说明>" <路径>...
set -u
MSG="$1"; shift
T=$(mktemp -d)
for p in "$@"; do [ -e "$p" ] && mkdir -p "$T/$(dirname "$p")" && cp -r "$p" "$T/$(dirname "$p")/"; done
git config user.name "bri-bot"; git config user.email "bri-bot@users.noreply.github.com"
for i in 1 2 3 4 5 6; do
  git fetch -q origin main && git reset -q --hard origin/main
  cp -r "$T"/. .
  git add "$@" 2>/dev/null
  if git diff --cached --quiet; then echo "no changes"; exit 0; fi
  git commit -qm "$MSG" && git push -q origin HEAD:main && { echo "pushed"; exit 0; }
  sleep $((i * 6))
done
echo "::error::push failed after 6 attempts"; exit 1
