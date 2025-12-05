#!/bin/bash

read -rp "Enter the path: " path

if [[ ! -d "$path" ]]; then
    echo "$path does not exist"
    echo "Program completing"
    exit 1
fi

echo
if (( $# == 1 )); then  
    if [[ -f "$path/$1" ]]; then
        echo "$1 - file exist"
    else
        echo "$1 - file does't exist"
    fi
fi
echo

offset="    "
result="Contents of the $(basename "$path") directory:\n"
for file in "$path"/*; do
    result+="{\n"

    file_info=$(stat "$file")
    file_type=$(awk '{if (FNR == 2) print $8}' <<< "$file_info")
    file_access=$(awk '{if (FNR == 4) print $1, $2}' <<< "$file_info")
    result+="${offset}File name: $(basename "$file")\n"
    
    result+="${offset}File type: "
    case $file_type in
    "regular")
        result+="regular file\n";;
    "directory")
        result+="directory\n";;
    *)
        result+="unknown file type\n";;
    esac

    result+="$offset${file_access}\n"
    result+="}\n"
done

printf "%b" "$result"
