#!/bin/bash

read -rp "Enter the path of diretory with .log files: " path

if [[ ! -d $path ]]; then
    echo "The directory does not exist"
    exit 1
fi

all_files=$(find "$path" -name "*.log")

while IFS= read -r file; do
    files_and_time+="Birth: $(stat -c %w "$file") File name: $(basename "$file")"$'\n'
done <<< "$all_files"

sorted=$(echo "$files_and_time" | sed '/^$/d' | sort -t" " -k2 -k3)

sorted5=$(echo "$sorted" | head -n5)

printf "The 5 oldest files:\n%s\n" "$sorted5"
