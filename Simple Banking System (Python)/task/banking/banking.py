import random
import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect("card.s3db")
cursor = conn.cursor()
# Create a table to store card numbers, PIN codes, and balance
cursor.execute("CREATE TABLE IF NOT EXISTS card (id INTEGER PRIMARY KEY, number TEXT, pin TEXT, balance INTEGER DEFAULT 0)")

def card_number_exists(card_number):
    cursor.execute("SELECT COUNT(*) FROM card WHERE number=?", (card_number,))
    return cursor.fetchone()[0] > 0

def login(card_number, pin):
    cursor.execute("SELECT COUNT(*) FROM card WHERE number=? AND pin=?", (card_number, pin))
    return cursor.fetchone()[0] > 0

def calculate_checksum(card_number_str):
    checksum = 0
    for i in range(len(card_number_str)):
        digit = int(card_number_str[i])
        if i % 2 == 0:
            doubled_digit = digit * 2
            if doubled_digit > 9:
                doubled_digit -= 9
            checksum += doubled_digit
        else:
            checksum += digit
    return (10 - checksum % 10) % 10

def update_card_number(card_number):
    card_number_str = str(card_number)[:-1]  # Exclude the last digit
    checksum = calculate_checksum(card_number_str)
    return checksum

def get_balance(card_number):
    cursor.execute("SELECT balance FROM card WHERE number=?", (card_number,))
    balance = cursor.fetchone()
    return balance[0] if balance else 0

def add_income(card_number, income):
    cursor.execute("UPDATE card SET balance = balance + ? WHERE number=?", (income, card_number))
    conn.commit()

def transfer_money(sender_card, receiver_card, amount):
    if sender_card == receiver_card:
        print("You can't transfer money to the same account!")
        return

    if not is_luhn_valid(receiver_card):
        print("Probably you made a mistake in the card number. Please try again!")
        return

    sender_balance = get_balance(sender_card)
    if sender_balance < amount:
        print("Not enough money!")
        return

    cursor.execute("SELECT * FROM card WHERE number=?", (receiver_card,))
    receiver_account = cursor.fetchone()
    if receiver_account is None:
        print("Such a card does not exist.")
        return

    cursor.execute("UPDATE card SET balance = balance - ? WHERE number=?", (amount, sender_card))
    cursor.execute("UPDATE card SET balance = balance + ? WHERE number=?", (amount, receiver_card))
    conn.commit()
    print("Success!")

def delete_account(card_number):
    cursor.execute("DELETE FROM card WHERE number=?", (card_number,))
    conn.commit()

def is_luhn_valid(card_number):
    digits = [int(digit) for digit in card_number]
    checksum = 0

    for i in range(len(digits) - 1, -1, -1):
        if (i + len(digits)) % 2 == 0:
            doubled_digit = digits[i] * 2
            checksum += doubled_digit if doubled_digit <= 9 else doubled_digit - 9
        else:
            checksum += digits[i]

    return checksum % 10 == 0

flag = 0
while True:
    if flag == 1:
        break
    else:
        print("1. Create an account")
        print("2. Log into account")
        print("0. Exit")

        choice = int(input())

        if choice == 1:
            first_six_digits = "400000"
            last_digit = str(random.randint(0, 9))  # Generate a random last digit

            # Generate the unique 9-digit number for the card
            unique_digits = "".join(str(random.randint(0, 9)) for _ in range(9))
            card_number = f"{first_six_digits}{unique_digits}{last_digit}"

            # Check if the card number already exists in the database
            while card_number_exists(card_number):
                unique_digits = "".join(str(random.randint(0, 9)) for i in range(9))
                card_number = f"{first_six_digits}{unique_digits}{last_digit}"

            # Calculate the new checksum
            checksum = update_card_number(card_number)

            # Update the last digit to satisfy the Luhn algorithm
            card_number = card_number[:-1] + str(checksum)

            # Insert the card details into the database
            cursor.execute("INSERT INTO card (number, pin) VALUES (?, ?)", (card_number, None))
            conn.commit()

            # Generate 4-digit PIN codes for the card
            pin = f"{random.randint(0, 9999):04d}"

            # Update the PIN code for the corresponding card number
            cursor.execute("UPDATE card SET pin=? WHERE number=?", (pin, card_number))
            conn.commit()

            # Output the card details
            print("Your card has been created")
            print("Your card number:")
            print(card_number)
            print("Your card PIN:")
            print(pin)

        elif choice == 2:
            card_number_ans = input("Enter your card number:")
            pin_card_ans = input("Enter your PIN:")
            cursor.execute("SELECT number, pin FROM card WHERE number=? AND pin=?", (card_number_ans, pin_card_ans))
            row = cursor.fetchone()

            if row is not None:
                print()
                print("You have successfully logged in!")
                print()

                while True:
                    if flag == 1:
                        break
                    else:
                        print("1. Balance")
                        print("2. Add income")
                        print("3. Do transfer")
                        print("4. Close account")
                        print("5. Log out")
                        print("0. Exit")

                        choice = int(input())

                    if choice == 1:
                        print()
                        print("Balance:", get_balance(card_number_ans))
                        print()
                    elif choice == 2:
                        income = int(input("Enter income: "))
                        add_income(card_number_ans, income)
                        print()
                        print("Income was added!")
                        print()
                    elif choice == 3:
                        print("Transfer")
                        receiver_card = input("Enter card number: ")
                        if receiver_card == card_number_ans:
                            print("You can't transfer money to the same account!")
                        elif not is_luhn_valid(receiver_card):
                            print("Probably you made a mistake in the card number. Please try again!")
                        elif not card_number_exists(receiver_card):
                            print("Such a card does not exist.")
                        else:
                            amount = int(input("Enter amount to transfer: "))
                            transfer_money(card_number_ans, receiver_card, amount)

                    elif choice == 4:
                        delete_account(card_number_ans)
                        print("The account has been closed!")
                        break

                    elif choice == 5:
                        print("You have successfully logged out!")
                        break

                    elif choice==0:
                        print("Bye!\n")
                        flag = 1
                        break
                    else:
                        print("This is not a valid choice. Please select a valid option.")
                        continue
            else:
                print()
                print("Wrong card number or PIN!")
                print()

        elif choice==0:
            print("Bye!")
            break
        else:
            print("This is not a valid choice. Please select a valid option.")
            continue

conn.close()
