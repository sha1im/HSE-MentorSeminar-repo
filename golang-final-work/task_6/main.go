package main

import "fmt"

func main() {
	var n int
	fmt.Scan(&n)
	positive, negative, zero := 0, 0, 0

	for i := 0; i < n; i++ {
		var number float64
		fmt.Scan(&number)
		if number > 0 {
			positive++
		} else if number < 0 {
			negative++
		} else {
			zero++
		}
	}

	fmt.Println("Positive numbers:", positive)
	fmt.Println("Negative numbers:", negative)
	fmt.Println("Zeros:", zero)
}
