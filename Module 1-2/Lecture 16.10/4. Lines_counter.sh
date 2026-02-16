#!/bin/bash

set -euo pipefail

read -rp "Введите путь к файлу: " path

if [[ ! -f "$path" ]]; then
	printf "%s - не существует\n" "$path"
	exit 1
fi

lines_num=$(wc -l "$path" | grep -o -E "^\s*[0-9]+")

printf "%s строк в файле\n" "$lines_num"
