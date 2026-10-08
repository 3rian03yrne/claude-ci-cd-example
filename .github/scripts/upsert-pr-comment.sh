#!/usr/bin/env bash
# Create or update this workflow's own comment on a PR.
#
#   upsert-pr-comment.sh <pr-number> <key> <body-file>
#
# The comment is tagged with a hidden <!-- key --> marker, and later runs edit the
# comment with that marker. `gh pr comment --edit-last` can't be used: it edits the
# bot's latest comment, so workflows sharing the bot overwrite each other's reports.
# Needs GH_TOKEN and GH_REPO in the environment.
set -euo pipefail

pr="$1"
marker="<!-- $2 -->"
body="$(printf '%s\n\n%s\n' "$marker" "$(cat "$3")")"

id="$(gh api --paginate "repos/${GH_REPO}/issues/${pr}/comments" \
  --jq ".[] | select(.user.login == \"github-actions[bot]\" and (.body | startswith(\"${marker}\"))) | .id" \
  | head -n 1)"

if [ -n "$id" ]; then
  gh api --method PATCH "repos/${GH_REPO}/issues/comments/${id}" -f body="$body" > /dev/null
  echo "Updated comment ${id}"
else
  gh pr comment "$pr" --repo "$GH_REPO" --body "$body"
fi
