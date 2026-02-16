#!/bin/bash

set -euo pipefail

read -p "Введите название файла: " file_name

if [ -f "$file_name" ]; then
	printf "Файл найден.\n"
else
	printf "Файл не существует.\n"
fi
