## Simple Command Line Calculator
## Professor, I talked to you about turning this in late due to connectivity issues in AZ.
## I am uncofrtable submitting this as my own work, its seems like AI is doing most of the lifting.
## I did make some modifications to the code, but not much, AI held my hand and led me through this.
## Again, I am not sure what the boundary is between my own work and the AI assisted work... perhaps that was the assigmnet.
## Lastly, my README.md is empty, I don't know what is suppoed to be in there, so I did not attach that.
## Can you aprise me of the AI situation on these assignments and what I shouls see in the REEADME file.
## Thank you, Mike

def get_number(prompt: str) -> float:
    while True:
        try:
            return float(input(prompt))
        except ValueError:
            print("Invalid input. Please enter a valid number.")

def add(a: float, b: float) -> float:
    return a + b
def subtract(a: float, b: float) -> float:
    return a - b
def multiply(a: float, b: float) -> float:
    return a * b
def divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Cannot divide by zero.")
    return a / b
def main():
    print("Simple Command Line Calculator")
    
    num1 = get_number("Enter the first number: ")
    
    print("Select operation:")
    print("1. Add")
    print("2. Subtract")
    print("3. Multiply")
    print("4. Divide")

    operation = input("Enter choice (1/2/3/4): ")

    num2 = get_number("Enter the second number: ")

    if operation == '1':
        result = add(num1, num2)
        print(f"{num1} + {num2} = {result}")
    elif operation == '2':
        result = subtract(num1, num2)
        print(f"{num1} - {num2} = {result}")
    elif operation == '3':
        result = multiply(num1, num2)
        print(f"{num1} * {num2} = {result}")
    elif operation == '4':
        try:
            result = divide(num1, num2)
            print(f"{num1} / {num2} = {result}")
        except ValueError as e:
            print(e)
    else:
        print("Invalid operation selected.")
if __name__ == "__main__":
    main()
