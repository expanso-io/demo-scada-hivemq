#!/usr/bin/env bash
set -euo pipefail

repo_dir=$(unset CDPATH; cd -- "$(dirname -- "$0")/.." && pwd)
cd "$repo_dir"

port=8877
base_url="http://127.0.0.1:${port}"
session=$(agent-browser session id \
  --scope worktree \
  --prefix pb-scada-hivemq)
server_pid=""

browser() {
  AGENT_BROWSER_SESSION="$session" agent-browser "$@"
}

cleanup() {
  browser close >/dev/null 2>&1 || true
  if [[ -n "$server_pid" ]] && kill -0 "$server_pid" 2>/dev/null; then
    kill "$server_pid"
    wait "$server_pid" 2>/dev/null || true
  fi
}
trap cleanup EXIT

if lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null; then
  echo "port $port is already in use" >&2
  exit 1
fi

mkdir -p .runtime/ui-check
uv run python -m http.server "$port" \
  --bind 127.0.0.1 \
  >.runtime/ui-check/server.log 2>&1 &
server_pid=$!

for _ in $(seq 1 30); do
  if curl --fail --silent "$base_url/dashboard/" >/dev/null; then
    break
  fi
  sleep 0.2
done
curl --fail --silent "$base_url/dashboard/" >/dev/null

browser open "$base_url/dashboard/?gate=1" >/dev/null
browser wait --text "Authenticated MQTT ingest" >/dev/null

for width in 320 400 768 1440; do
  browser set viewport "$width" 900 >/dev/null
  for theme in light dark; do
    browser eval \
      "document.documentElement.dataset.theme='$theme'" \
      >/dev/null
    browser eval \
      "({overflow:document.documentElement.scrollWidth>document.documentElement.clientWidth})" \
      | jq -e '.overflow == false' >/dev/null
  done
done

for width in 320 1440; do
  browser set viewport "$width" 900 >/dev/null
  for theme in light dark; do
    browser eval \
      "document.documentElement.dataset.theme='$theme'" \
      >/dev/null
    browser a11y --tags wcag2a,wcag2aa --json \
      | jq -e \
        '.data.violations == [] and .data.incomplete == []' \
        >/dev/null
  done
done

browser set viewport 1440 900 >/dev/null
browser scrollintoview '#explorer' >/dev/null
before_scroll=$(browser eval 'Math.round(scrollY)')
browser press ArrowRight >/dev/null
browser wait --text "Sparkplug B decode" >/dev/null
after_scroll=$(browser eval 'Math.round(scrollY)')
[[ "$before_scroll" == "$after_scroll" ]]

browser click '[data-copy-target="stage-input"]' >/dev/null
browser wait --text "Copied" >/dev/null
browser eval \
  "document.querySelector('[data-copy-target=\"stage-input\"] + .action-result').textContent" \
  | jq -e '. == "Copied"' >/dev/null

browser eval \
  "document.querySelector('[data-copy-target=\"stage-input\"]').dataset.copyTarget='missing-target'" \
  >/dev/null
browser click '[data-copy-target="missing-target"]' >/dev/null
browser wait --text "Copy failed" >/dev/null

browser click '#download-fixture' >/dev/null
browser wait --text "Downloaded" >/dev/null
browser eval \
  "document.querySelector('#download-fixture + .action-result').textContent" \
  | jq -e '. == "Downloaded"' >/dev/null

browser eval \
  "URL.createObjectURL=()=>{throw new Error('forced failure')};document.querySelector('#download-pipeline').click()" \
  >/dev/null
browser wait --text "Download failed" >/dev/null

cleanup
server_pid=""
trap - EXIT

if lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null; then
  echo "UI check left port $port listening" >&2
  exit 1
fi

echo "UI checks passed at 320, 400, 768, and 1440 pixels"
