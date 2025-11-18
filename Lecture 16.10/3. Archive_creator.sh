#!/usr/bin/env bash
set -Eeuo pipefail

read -rp "Укажите директорию или файл, которую хотите поместить в архив: " path

# Проверяем, существует ли путь
if [[ ! -e "$path" ]]; then
  printf "%s - не существует\n" "$path"
  exit 1
fi

base=$(basename -- "$path")
to_save_path=$(dirname -- "$path")
suffix="_backup-$(date +'%Y-%m-%d').tar.gz"
full_path="$to_save_path/${base}${suffix}"

# Создаём архив
tar -czf "$full_path" -C "$to_save_path" "$base"

printf "\nФайл или директория '%s' успешно сохранён(а) в архив:\n%s\n" "$path" "$full_path"
