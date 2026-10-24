package main

import "fmt"

func main() {
	var n int
	fmt.Scan(&n)
	if n <= 0 {
		fmt.Println("N must be positive")
		return
	}

	var number float64
	fmt.Scan(&number)
	minimum, maximum := number, number

	for i := 1; i < n; i++ {
		fmt.Scan(&number)
		if number < minimum {
			minimum = number
		}
		if number > maximum {
			maximum = number
		}
	}

	fmt.Println("Maximum:", maximum)
	fmt.Println("Minimum:", minimum)
}
