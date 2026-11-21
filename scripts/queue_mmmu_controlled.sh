#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

usage() {
    cat <<'EOF'
Usage: scripts/queue_mmmu_controlled.sh [--dry-run] [pilot|context|seeds|full ...]
Default queue: pilot context seeds. Pass full explicitly to include the 900q pair.
Uses the webhook configured in this script. Override it with DISCORD_WEBHOOK_URL
or DISCORD_WEBHOOK_FILE. A dry run previews commands without notifications.
EOF
}

dry_run=false
case "${1:-}" in
    -h|--help) usage; exit 0 ;;
    --dry-run) dry_run=true; shift ;;
esac
modes=("$@")
if (( ${#modes[@]} == 0 )); then modes=(pilot context seeds); fi
declare -A seen=()
for mode in "${modes[@]}"; do
    case "$mode" in
        pilot|context|seeds|full) ;;
        *) usage >&2; exit 2 ;;
    esac
    if [[ -v 'seen[$mode]' ]]; then
        printf 'Duplicate mode: %s\n' "$mode" >&2
        exit 2
    fi
    seen["$mode"]=1
done

if [[ $dry_run == true ]]; then
    for mode in "${modes[@]}"; do
        printf '\n[%s]\n' "$mode"
        bash scripts/run_mmmu_controlled.sh "$mode" --dry-run
    done
    exit 0
fi

set +x
webhook="${DISCORD_WEBHOOK_URL:-}"
if [[ -z $webhook && -n ${DISCORD_WEBHOOK_FILE:-} ]]; then
    webhook=$(<"$DISCORD_WEBHOOK_FILE")
fi
if [[ -z $webhook ]]; then webhook='https://discord.com/api/webhooks/1571206579397595227/z6H2IUXt5MBiRv7b2YQmniD7QXEpymEoG4ioSQEDx_Lvrcpm_sTzu5o_CdQk63PsRA0m'; fi
unset DISCORD_WEBHOOK_URL
if [[ ! $webhook =~ ^https://(discord\.com|discordapp\.com)/api/webhooks/[0-9]+/[A-Za-z0-9_-]+$ ]]; then
    printf 'Set DISCORD_WEBHOOK_URL or DISCORD_WEBHOOK_FILE to a Discord webhook.\n' >&2
    exit 2
fi

output="${MMMU_CONTROLLED_OUT:-runs/controlled_legacy_cot}"
mkdir -p "$output"
exec 9>"$output/.queue.lock"
flock -n 9 || { printf 'A queue is already running in %s\n' "$output" >&2; exit 1; }

notify() {
    local message="$1" payload
    payload=$(printf '{"content":"%s","allowed_mentions":{"parse":[]}}' "$message")
    if ! printf 'url = "%s"\n' "$webhook" | curl --disable --config - \
        --silent --fail --connect-timeout 5 --max-time 15 --output /dev/null \
        --header 'Content-Type: application/json' --data-binary "$payload"; then
        printf 'Discord notification failed for %s\n' "$message" >&2
    fi
}

for mode in "${modes[@]}"; do
    started=$SECONDS
    printf '[%s] Starting %s\n' "$(date -Is)" "$mode"
    if bash scripts/run_mmmu_controlled.sh "$mode"; then
        printf '[%s] Completed %s\n' "$(date -Is)" "$mode"
        notify "MMMU $mode completed ($((SECONDS - started))s)."
    else
        result=$?
        printf '[%s] %s failed (exit %s). Queue stopped.\n' "$(date -Is)" "$mode" "$result" >&2
        notify "MMMU $mode failed (exit $result, $((SECONDS - started))s). Queue stopped."
        exit "$result"
    fi
done
