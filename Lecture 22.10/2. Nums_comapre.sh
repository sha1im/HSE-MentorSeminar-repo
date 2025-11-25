#!/bin/bash

if (( $1 > $2 )); then
	echo "$1 bigger than $2"
elif (( $1 < $2 )); then 
	echo "$1 less than $2"
else
	echo "$1 equals $2"
fi
