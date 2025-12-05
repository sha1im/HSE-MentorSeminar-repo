#!/bin/bash

set -euo pipefail

read -rp "Enter num: " num

if (( num > 0 )); then
    echo "$num is positive"

    i=0
    while (( i <= $num )); do
        printf "%d " "$((i++))"
    done
    echo
else
    echo "$num is negative"
fi
