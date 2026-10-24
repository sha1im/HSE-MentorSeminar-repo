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
	var minimum, maximum int
	even, odd := 0, 0

	for i := 0; i < n; i++ {
		var number int
		fmt.Scan(&number)
		sum += float64(number)
		if i == 0 || number < minimum {
			minimum = number
		}
		if i == 0 || number > maximum {
			maximum = number
		}
		if number%2 == 0 {
			even++
		} else {
			odd++
		}
	}

	fmt.Println("Sum:", sum)
	fmt.Println("Average:", sum/float64(n))
	fmt.Println("Maximum:", maximum)
	fmt.Println("Minimum:", minimum)
	fmt.Println("Even numbers:", even)
	fmt.Println("Odd numbers:", odd)
}
