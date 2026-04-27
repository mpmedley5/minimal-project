## CLI Prototype - Michael Medley

## A single Python script file containing a simple CLI application.
## Application must be able to:
## 1) Add a new item
## 2) List all items
## 3) Exit

## All data is stored in a single global variable (ITEMS) while the program runs.

## Single global variable for all stored data

ITEMS = []

def add_item() -> None:
    # Prompt the user for a new item and add it to the global ITEMS list.
    item = input("Enter a new item to add to the main menu: ").strip()

    if not item:
        print("Blank input, nothing was added to the menu)")
        return

    ITEMS.append(item)
    print(f'Added: "{item}"')


def list_items() -> None:
    #Print all items currently stored in the global ITEMS list.
    if not ITEMS:
        print("No items have been added yet.")
        return

    print("\nCurrent Items:")
    for index, item in enumerate(ITEMS, start=1):
        print(f"{index}. {item}")


def show_menu() -> None:
    #Display the main menu options.
    print("\n=== Main Menu ===")
    print("1) Add a new menu item")
    print("2) List all menu items")
    print("3) Learn Python")
    print("4) Exit program")



def main() -> None:
    #Main program loop.
    print("Comman-Line Application Prototype")

    while True:
        show_menu()
        choice = input("Choose an option (1-4): ").strip()

        if choice == "1":
            add_item()
        elif choice == "2":
            list_items()
        elif choice == "3":
            print("Learn Python - Take INFO 6200 from Professor Riskas at UVU.")
        elif choice == "4":
            print("Exiting program.")
            break
        else:
            print("Invalid choice. Please enter 1, 2, 3, or 4.")

if __name__ == "__main__":
    main()
