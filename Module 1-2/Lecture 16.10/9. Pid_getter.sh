#!/bin/bash

set -euo pipefail

if (( $# == 0 )); then
	printf "Отсутствует команда для запуска\n"
	exit 1
fi

log_name_getter() {
	local base="${1}_$(date -I)"
	local log_name="$base"
	local i=0
	
	while [[ -f "${log_name}.log" ]]; do
		i=$((i + 1))

		if (( i >= 100 )); then
			printf "Превышен лимит лог файлов\n"
			exit 2
		fi

		log_name="${base}($i)"
	done
	
	echo "${log_name}.log"
}

log_name=$( log_name_getter "pid_get_log" )

"$@" >"$log_name" 2>&1 &
pid=$!

printf "PID: %s\n" "$pid"
