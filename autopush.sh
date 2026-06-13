#!/bin/bash
# Auto-push changes to GitHub

TOKEN="${GIT_TOKEN:-$GITHUB_PERSONAL_ACCESS_TOKEN}"

if [ -z "$TOKEN" ]; then
    echo "[autopush] GIT_TOKEN not set, skipping push."
    exit 0
fi

REPO_URL="https://${TOKEN}@github.com/techspider-alt/-_-.git"
BRANCH="${UPSTREAM_BRANCH:-main}"

git config user.email "bot@ronaldomusic.replit" 2>/dev/null
git config user.name "RONALDO MUSIC Bot" 2>/dev/null

git remote set-url origin "$REPO_URL" 2>/dev/null || git remote add origin "$REPO_URL"

git add -A
git diff --cached --quiet && echo "[autopush] Nothing to commit." && exit 0

git commit -m "🎵 Auto-sync from Replit: $(date '+%Y-%m-%d %H:%M:%S')"
git push origin HEAD:"$BRANCH" && echo "[autopush] ✅ Pushed to GitHub successfully." || echo "[autopush] ❌ Push failed — check GIT_TOKEN permissions."
