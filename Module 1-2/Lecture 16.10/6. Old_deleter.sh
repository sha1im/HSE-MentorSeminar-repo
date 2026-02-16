#!bin/bash

set -euo pipefail

read -rp "Укажите путь к директории: " path

if [[ ! -d "$path" ]]; then
    printf "%s — директория не существует\n" "$path"
    exit 1
fi

line=$(printf "%0.s-" {1..50})

printf "Следующие файлы будут удалены:\n"

printf "%s\n" "$line"
find "$path" -type f -mtime +7
printf "%s\n" "$line"

while true; do
	read -rp "Согласны ли вы с удалением файлов? (Y/N): " answer
	if [[ $answer == "Y" ]]; then
		find "$path" -type f -mtime +7 -delete
		printf "Файлы с изменениями позже 7 дней удалены успешно.\n"
		break
	elif [[ $answer == "N" ]]; then
		printf "Удаление файлов отменено.\n"
		break
	else 
		printf "Введен некорретный символ, попробуйте еще раз.\n"
	fi
done
