#!/bin/bash

read -rp "Enter the path: " path

if [[ ! -d "$path" ]]; then
    echo "Directory doesn't exist"
    exit 1
fi

sum=0; renamed=0
for file in "$path"/*; do
    (( ++sum ))
   
    name=$(basename "$file")
    lower_name=${name,,}
    path_lower=$(dirname "$file")/$lower_name

    if [[ ! -f "$path_lower" ]]; then
        printf "Rename file %s to file %s? (Y/N)\n" "$name" "$lower_name"
        
        while true; do
            read answer

            case $answer in
                "Y")
                    mv "$file" "$path_lower"
                    (( ++renamed ))
                    break;;
                "N")
                    break;;
                *)
                    echo "Unknown command, please try again. Accepted characters are Y(yes) or N(no).\n"
            esac
        done
    fi
done

echo "$renamed of $sum files successfully renamed"
