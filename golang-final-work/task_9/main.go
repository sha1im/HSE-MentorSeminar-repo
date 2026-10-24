package main

import "fmt"

func main() {
	var balance float64
	var action int
	fmt.Println("Enter the balance:")
	fmt.Scan(&balance)
	if balance < 0 {
		fmt.Println("The balance cannot be negative.")
		return
	}

	fmt.Println("1. Check balance")
	fmt.Println("2. Top up balance")
	fmt.Println("3. Withdraw funds")
	fmt.Scan(&action)

	switch action {
	case 1:
		fmt.Println("Balane:", balance)
	case 2, 3:
		var amount float64
		fmt.Println("Enter the sum:")
		fmt.Scan(&amount)
		if amount <= 0 {
			fmt.Println("Sum must be posirive")
			return
		}
		if action == 2 {
			balance += amount
		} else {
			if amount > balance {
				fmt.Println("Insufficient funds")
				return
			}
			balance -= amount
		}
		fmt.Println("Balance:", balance)
	default:
		fmt.Println("Unknown action")
	}
}
