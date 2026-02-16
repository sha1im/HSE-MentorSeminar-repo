#!/bin/bash

MATRIX="sKih67RNp#4E0DWZtuOYc3@1Xx5zqHwVy!gQ9jUvBka&L*8AISPTmbMG-f_e2lnrCFJdo$"

length=$1

while (( ${i:=0} < length )); do

    password="$password${MATRIX:$((RANDOM%${#MATRIX})):1}"
    (( i+=1 ))

done

echo "Your generated password: $password"
