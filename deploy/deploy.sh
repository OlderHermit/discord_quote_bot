#!/usr/bin/env bash

set -euo pipefail

# --- configuration -----------------------------------------------------------

REPO_DIR="${REPO_DIR:-/opt/discord_quote_bot}"
SERVICE="${SERVICE:-quotebot}"
VENV="${VENV:-$REPO_DIR/.venv}"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8000/health}"
HEALTH_TIMEOUT="${HEALTH_TIMEOUT:-45}"
LOCK_FILE="${LOCK_FILE:-$HOME/.quotebot-deploy.lock}"

TARGET_SHA="${1:-}"
DIST_TARBALL="${2:-}"

if [ -z "$TARGET_SHA" ]; then
    echo "usage: $0 <commit-sha> [front-dist-tarball]" >&2
    exit 64
fi

log() { printf '[%s] %s\n' "$(date -Is)" "$*"; }
die() { log "ERROR: $*" >&2; exit 1; }

# --- serialise deploys -------------------------------------------------------

exec 9>"$LOCK_FILE"
flock -n 9 || die "another deploy is already running"

# --- preflight ---------------------------------------------------------------

if [ -n "$DIST_TARBALL" ]; then
    DIST_TARBALL="$(readlink -f "$DIST_TARBALL")"
    [ -f "$DIST_TARBALL" ] || die "no tarball at $DIST_TARBALL"
fi

cd "$REPO_DIR" || die "no repo at $REPO_DIR"
[ -x "$VENV/bin/python" ] || die "no virtualenv at $VENV"

PREV_SHA="$(git rev-parse HEAD)"

log "fetching"
git fetch --prune --quiet origin

git cat-file -e "${TARGET_SHA}^{commit}" 2>/dev/null \
    || die "commit $TARGET_SHA not found after fetch"

log "deploying ${PREV_SHA:0:8} -> ${TARGET_SHA:0:8}"

# --- rollback ----------------------------------------------------------------

DIST_MOVED=0

rollback() {
    trap - ERR EXIT              # never re-enter this
    set +e
    log "deploy failed, rolling back to ${PREV_SHA:0:8}"

    git checkout --force --quiet "$PREV_SHA"

    if [ "$DIST_MOVED" -eq 1 ] && [ -d front/dist.prev ]; then
        rm -rf front/dist
        mv front/dist.prev front/dist
    fi

    printf '%s\n' "$PREV_SHA" > REVISION

    if ! git diff --quiet "$PREV_SHA" "$TARGET_SHA" -- requirements.txt; then
        log "restoring previous dependencies"
        "$VENV/bin/pip" install --quiet -r requirements.txt
    else
        log "requirements unchanged no need to restore environ"
    fi
    sudo systemctl restart "$SERVICE"

    if wait_healthy 30; then
        log "rolled back to ${PREV_SHA:0:8}, service healthy"
    else
        log "ROLLBACK ALSO FAILED - service is down, manual intervention needed"
    fi
    exit 1
}

wait_healthy() {
    local deadline=$(( SECONDS + ${1:-$HEALTH_TIMEOUT} ))
    while [ "$SECONDS" -lt "$deadline" ]; do
        if curl -fsS --max-time 2 "$HEALTH_URL" >/dev/null 2>&1; then
            return 0
        fi
        sleep 1
    done
    return 1
}

trap rollback ERR

# --- checkout ----------------------------------------------------------------

git checkout --force --quiet "$TARGET_SHA"
printf '%s\n' "$TARGET_SHA" > REVISION

# --- dependencies ------------------------------------------------------------

if ! git diff --quiet "$PREV_SHA" "$TARGET_SHA" -- requirements.txt; then
    log "requirements.txt changed, installing"
    "$VENV/bin/pip" install -r requirements.txt
else
    log "requirements unchanged, skipping pip"
fi

# --- front end ---------------------------------------------------------------

if [ -n "$DIST_TARBALL" ]; then
    log "unpacking front build"
    rm -rf front/dist.prev
    [ -d front/dist ] && mv front/dist front/dist.prev && DIST_MOVED=1
    mkdir -p front/dist
    tar -xzf "$DIST_TARBALL" -C front/dist
fi

# --- restart and verify ------------------------------------------------------

log "restarting $SERVICE"
sudo systemctl restart "$SERVICE"

if ! wait_healthy "$HEALTH_TIMEOUT"; then
    log "health check did not pass within ${HEALTH_TIMEOUT}s"
    rollback
fi

# Confirm the healthy process is actually running the new code, not a stale one.
RUNNING_SHA="$($VENV/bin/python -c '
import json, urllib.request, os
with urllib.request.urlopen(os.environ["HEALTH_URL"], timeout=5) as r:
    print(json.load(r).get("commit", ""))
' 2>/dev/null || true)"

if [ -n "$RUNNING_SHA" ] && [ "$RUNNING_SHA" != "$TARGET_SHA" ]; then
    log "health reports commit ${RUNNING_SHA:0:8}, expected ${TARGET_SHA:0:8}"
    rollback
fi

# --- done --------------------------------------------------------------------

trap - ERR
rm -rf front/dist.prev
[ -n "$DIST_TARBALL" ] && rm -f "$DIST_TARBALL"

log "deployed ${TARGET_SHA:0:8} successfully"