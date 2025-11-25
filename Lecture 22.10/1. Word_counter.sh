#/bin/bash

echo $(grep -wo "$1" "$2" | wc -l)
