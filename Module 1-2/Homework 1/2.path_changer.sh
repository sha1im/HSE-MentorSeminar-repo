#!/bin/bash

set -eou pipefail

if (( $# < 1 )); then
    echo "Error: arguments empty." >&2
    exit 1
fi

if [[ ! -d "$1" ]]; then
    echo "$1 - directory dosn't exist" >&2
    exit 2
fi

printf "PATH before change:\n%s\n" "$(echo "$PATH" | sed 's/:/\n/g')"

PATH+=":$1"

printf "PATH after change:\n%s\n" "$(echo "$PATH" | sed 's/:/\n/g')"
