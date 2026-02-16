#!/bin/bash

ping -q -c3 -i0.002 -W1 "$1" >/dev/null 2>&1

err_code=$?

if (( err_code == 0 )); then
    echo "The server is available."
else
    echo "The server is not available. Error code: $err_code"
fi
