package main

import "fmt"

func main() {
	var n int
	fmt.Scan(&n)
	if n <= 0 {
		fmt.Println("N must be positive")
		return
	}

	var sum float64
	for i := 1; i <= n; i++ {
		sum += float64(i)
	}

	fmt.Println("Sum:", sum)
	fmt.Println("Average:", sum/float64(n))
}
