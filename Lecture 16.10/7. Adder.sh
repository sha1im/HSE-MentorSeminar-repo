#!/bin/bash

set -euo pipefail

add() {
	PATTERN='^(0|-?[1-9][0-9]*)$'

	if ! [[ $1 =~ $PATTERN && $2 =~ $PATTERN ]]; then
		return 1
	fi

	echo $(( $1 + $2 ))
}

read -rp "Введите 2 числа: " x y

if ! sum=$(add "$x" "$y") ; then
	echo "Ошибка: неверные аргументы"
    exit 1
fi

printf "%s + %s = %s\n" "$x" "$y" "$sum"
