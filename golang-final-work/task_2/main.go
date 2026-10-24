package main

import (
	"fmt"
	"strings"
	"os"
)

func AnalyzeNumber(num int) string {
	var b strings.Builder

	if num > 0 {
		b.WriteString("Is positive\n")
	} else if num < 0 {
		b.WriteString("Is negative\n")
	} else {
		b.WriteString("Is zero\n")
	}

	if num%2 == 0 {
		b.WriteString("Even number\n")
	} else {
		b.WriteString("An odd number\n")
	}

	if num%5 == 0 {
		b.WriteString("The number is divisible by 5\n")
	} else {
		b.WriteString("The number is not divisible by 5\n")
	}

	if num%3 == 0 {
		b.WriteString("The number is divisible by 3\n")
	} else {
		b.WriteString("The number is not divisible by 3\n")
	}

	return b.String()
}

func main() {
	var num int

	_, err := fmt.Scan(&num)
	if err != nil {
		fmt.Printf("scan num: %v\n", err)
		os.Exit(1)
	}

	fmt.Println(AnalyzeNumber(num))
}
