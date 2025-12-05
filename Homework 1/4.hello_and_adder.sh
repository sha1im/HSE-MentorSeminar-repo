#!/bin/bash

set -euo pipefail

sum() {
    if (( $# < 2)); then
        printf "sum function error:\nThe function require 2 arguments. Received: $#\n"
        exit 1
    fi

    echo "$(( $1 + $2 ))"
}

prefix_hello_adder() {
    if (( $# == 0 )); then
        printf "prefix_hello_adder function error:\nNo function arguments.\n" >&2
        exit 2
    fi

    echo "Hello, "$1""
}

start_word=Egor
end_word=$(prefix_hello_adder "$start_word")

echo "$end_word"

first_num=24
second_num=26
result=$(sum first_num second_num)

echo "$result"
