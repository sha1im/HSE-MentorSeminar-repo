#!/bin/bash

command1() {
    sleep 1
}

command2() {
    sleep 2
}

command3() {
    sleep 3
}

start_t=$(date +%s%N)

echo "Running commands."

command1 &
echo "Command 1 launched"
command2 &
echo "Command 2 launched"
command3 &
echo "Command 3 launched"

wait

echo "All commands were executed successfully."

end_t=$(date +%s%N)

echo "Execution time: $(( (end_t - start_t) / 1000000 ))ms"
