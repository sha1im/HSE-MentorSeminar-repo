#!/bin/bash

get_changes_time() {
    echo "$(stat $1 | grep -e Modify -e Change | cut -f 2,3)"
}

tracked_file=$1
start_time=$(get_changes_time $tracked_file)

printf "%s file tracked. Start time:\n%s\n" "$tracked_file" "$start_time"

while true; do
    sleep 5
    check_time=$(get_changes_time $tracked_file)
    if [[ "$start_time" != "$check_time" ]]; then
        printf "File was changed. Old changed time:\n%s\n" "$start_time"

        printf "New changed time:\n%s\n" "$check_time"
        start_time="$check_time"
    fi
done
