#!/bin/bash

set -euo pipefail

backup_adder() {
	for file in "$1"/*
	do
	
	if [[ -f "$file" ]]; then
		file_name=$(basename -- "$file")
		mv "$file" "$1/backup_$file_name"
	fi
	
	done
}

read -rp "Укажите директорию: " path

if [[ ! -d "$path" ]]; then
	printf "%s - директория не существует" "$path"
	exit 1
fi

backup_adder "$path"

printf "Файлы успешно переименованы.\n"
