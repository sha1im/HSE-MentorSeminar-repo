package main

import (
	"errors"
	"fmt"
	"os"
)

func Calculate(n1 float64, n2 float64, op string) (float64, error) {
	if len(op) == 0 {
		return -1, errors.New("empty operation")
	}

	switch op {
	case "+":
		return n1 + n2, nil
	case "-":
		return n1 - n2, nil
	case "*":
		return n1 * n2, nil
	case "/":
		if n2 == 0 {
			return -1, errors.New("division by zero")
		}
		return n1 / n2, nil
	default:
		return -1, errors.New("unknown operation")
	}
}

func main() {
	var n1, n2 float64
	var op string

	_, err := fmt.Scan(&n1, &n2, &op)
	if err != nil {
		fmt.Printf("scan: %v\n", err)
		os.Exit(1)
	}

	res, err := Calculate(n1, n2, op)
	if err != nil {
		fmt.Printf("calculate: %v\n", err)
		os.Exit(2)
	}

	fmt.Println(res)
}
