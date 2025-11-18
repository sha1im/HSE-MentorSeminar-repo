#!/bin/bash

set -euo pipefail

printf "%s\n" "Мониторинг памяти активирован.
Будет выведено уведомление при заполнении
дискового пространства более, чем на 80%"

while true; do
	sleep 5
	
	mem_use=$(df -P | awk '$6 == "/" { gsub("%", "", $5); print $5}')

	if (( mem_use > 80 )); then
		printf "Дисковое пространство заполненно на %s%%\n" "$mem_use"
	fi
done
