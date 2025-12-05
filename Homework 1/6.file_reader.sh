#!/bin/bash

if (( $# == 0 )); then
    echo "The script is required at least one argument."
    exit 1
fi

if [[ ! -f "$1" ]]; then
    echo "The file "$1" doesn't exist"
    exit 2
fi

wc -l < "$1" >> output.txt

ls non_exit_file 2>>error.log
