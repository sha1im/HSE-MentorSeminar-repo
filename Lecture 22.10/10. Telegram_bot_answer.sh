#!/bin/bash

OFFSET_FILE="offset.txt"

query_error() {
    echo "Checking for update errors." >&2 
    echo "$1" | jq -e '.ok != true' >/dev/null
}

get_updates_timeout30() {
    local offset="$1"

    echo "Getting updates via chats (offset=$offset)." >&2
    local result=$(curl -s "${url}/getUpdates?timeout=30&offset=${offset}")
    echo "Updates received." >&2

    # логирование
    echo "===== OFFSET $offset | $(date) =====" >> updates.log
    echo "$result" | jq >> updates.log
    echo >> updates.log

    if ! query_error "$result"; then
        echo "No error" >&2
        echo "$result"
    else
        echo "Requesting updates error" >&2
        echo "Closing the connection" >&2
        exit 150
    fi
}

query_result_length() {
    echo "$1" | jq -r '.result | length'
}

send_message() {
    curl -s -X POST "${url}/sendMessage" \
        -d chat_id="$1" \
        -d text="$2" | jq >>send_message.log
}

save_offset() {
    echo "$1" > "$OFFSET_FILE"
}

load_offset() {
    if [[ -f "$OFFSET_FILE" ]]; then
        cat "$OFFSET_FILE"
    else
        echo 0
    fi
}

process_results() {
    local json="$1"
    local results_count=$(query_result_length "$json")

    for ((i=0; i < "$results_count"; ++i)); do
        local command=$(echo "$json" | jq -r ".result[$i].message.text")
        local chatid=$(echo "$json" | jq -r ".result[$i].message.chat.id")

        case "$command" in
        "Дата")
            send_message "$chatid" "$(date +%F)" &
            ;;
        "Время")
            send_message "$chatid" "$(date +%T)" &
            ;;
        "Дата и время")
            send_message "$chatid" "$(date +"%F %T")" &
            ;;
        *)
            send_message "$chatid" "Unknown message" &
        esac
    done

    wait

    local last_update_id=$(echo "$json" | jq '.result[-1].update_id')
    local new_offset=$(( last_update_id + 1 ))

    save_offset "$new_offset"

    echo "Offset updated to $new_offset" >&2
}

read -rsp "Enter your bot id token: " token
url="https://api.telegram.org/bot${token}"

offset=$(load_offset)
echo "Starting with offset=$offset" >&2

while true; do
    echo "Connecting..." >&2
    
    result=$(get_updates_timeout30 "$offset")
    count=$(query_result_length "$result")
    
    if (( $count > 0 )); then    
        echo "Processing results ($count updates)." >&2
        process_results "$result"
        offset=$(load_offset)
        echo "Updates processed" >&2
    else
        echo "No updates" >&2
    fi

    printf "\n=====END OF ITERATION=====\n"
done
