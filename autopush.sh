#!/bin/bash
# Auto-push changes to GitHub using GIT_TOKEN

if [ -z "$GIT_TOKEN" ]; then
    echo "[autopush] GIT_TOKEN not set, skipping push."
    exit 0
fi

REPO_URL="https://${GIT_TOKEN}@github.com/mystricman0-cell/DARK-MUSICS.git"
BRANCH="${UPSTREAM_BRANCH:-main}"

git config user.email "bot@ronaldomusic.replit" 2>/dev/null
git config user.name "RONALDO MUSIC Bot" 2>/dev/null

git add -A
git diff --cached --quiet && echo "[autopush] Nothing to commit." && exit 0

git commit -m "Auto-push from Replit: $(date '+%Y-%m-%d %H:%M:%S')"
git push "$REPO_URL" HEAD:"$BRANCH" && echo "[autopush] ✅ Pushed to GitHub successfully." || echo "[autopush] ❌ Push failed."
