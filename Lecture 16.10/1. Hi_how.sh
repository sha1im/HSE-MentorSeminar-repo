#!/bin/bash

set -euo pipefail

read -p "Введите ваше имя: " name

while true; do
	read -p "Ведите ваш возраст: " age
	if [[ "$age" =~ ^[0-9]+$ ]]; then
		break
	else
		echo "Возраст введен в некорректном формате. Попробуйте еще раз."
	fi
done

echo "Привет, $name! Через год тебе будет $((age + 1)) лет."
