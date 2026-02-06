## CLI Prototype Domain Menu- Michael Medley

## A single Python script file containing a simple CLI application.
## Application must be able to:
## 1) Select CompTIA domain from a static list
## 2) List current domain
## 3) Exit

## All data is stored in a single global variable (ITEMS) while the program runs.

## Single global variable for all stored data

# Single global variable holding all in-memory data for this prototype
APP_STATE = {
    "domains": [
        "CompTIA A+ Hardware",
        "CompTIA A+ Software",
        "CompTIA Network+",
        "CompTIA Security+",
        "CompTIA Linux+",
        "CompTIA Pentest+",
        "CompTIA CySA+",
   ],
    "current_domain": None,
    "saved_qa_pairs": []
}

def show_chatbot_invitation() -> None:
    """Display the chatbot invitation after domain selection."""
    print(f"\nYou can ask me questions about: {APP_STATE['current_domain']}\n")


def start_chat_session() -> None:
    """Start an interactive chat session for the selected domain."""
    last_question = None
    last_answer = None
    
    print("\n--- Chat Commands ---")
    print("Type 'save' to save the last Q&A")
    print("Type 'list' to see last 10 saved Q&A pairs")
    print("Type 'exit' to return to main menu")
    print("--- End Commands ---\n")
    
    while True:
        user_input = input("You: ").strip()
        
        # Handle special commands
        if user_input.lower() == "exit":
            print("\nReturning to main menu...\n")
            break
        elif user_input.lower() == "save":
            if last_question and last_answer:
                APP_STATE["saved_qa_pairs"].append({
                    "question": last_question,
                    "answer": last_answer,
                    "domain": APP_STATE["current_domain"]
                })
                print(f"✓ Saved: '{last_question}'\n")
            else:
                print("No Q&A pair to save yet. Ask a question first.\n")
            continue
        elif user_input.lower() == "list":
            if APP_STATE["saved_qa_pairs"]:
                recent_pairs = APP_STATE["saved_qa_pairs"][-10:]
                print("\n=== Last 10 Saved Q&A Pairs ===")
                for i, pair in enumerate(recent_pairs, start=1):
                    print(f"\n{i}. [{pair['domain']}]")
                    print(f"   Q: {pair['question']}")
                    print(f"   A: {pair['answer']}")
                print("\n=== End of List ===\n")
            else:
                print("No saved Q&A pairs yet.\n")
            continue
        elif user_input.lower() in ["quit", "back"]:
            print("\nReturning to main menu...\n")
            break
        
        if not user_input:
            continue
        
        # Store the question
        last_question = user_input
        
        # Placeholder for chatbot response
        last_answer = f"I understand you want to know about \"{user_input}\" in {APP_STATE['current_domain']}. (Chatbot response would go here)"
        print(f"Newman: {last_answer}\n")


def choose_domain() -> None:
    #Let the user select a domain from the static domain list.
    print("\n=== Choose a Domain ===")

    for index, domain in enumerate(APP_STATE["domains"], start=1):
        print(f"{index}) {domain}")

    choice = input(f"Select a domain (1-{len(APP_STATE['domains'])}): ").strip()

    if not choice.isdigit():
        print("Please enter a number.")
        return

    choice_num = int(choice)

    if choice_num < 1 or choice_num > len(APP_STATE["domains"]):
        print("That selection is out of range.")
        return

    APP_STATE["current_domain"] = APP_STATE["domains"][choice_num - 1]
    print(f'Current domain set to: {APP_STATE["current_domain"]}')
    
    # Show invitation and start chat session after domain selection
    show_chatbot_invitation()
    start_chat_session()


def show_current_domain() -> None:
    """Display the currently selected domain."""
    if APP_STATE["current_domain"] is None:
        print("No domain selected yet.")
    else:
        print(f"Current domain: {APP_STATE['current_domain']}")


def show_menu() -> None:
    """Display the main menu options."""
    print("\n==============================================================")
    print("Welcome to the Information Technology student learning chatbot")
    print("==============================================================")
    print("Hello, I am Newman, your AI teaching assistant")
    print("I am here to help you learn course content for TEIT courses")
    print("You can ask me questions about specific CompTIA course content")
    print("\n1) Choose a domain")
    print("2) Show current domain")
    print("3) Exit program")


def main() -> None:
    """Main program loop."""
    print("Command-Line Application Prototype - Domain Selector")

    while True:
        show_menu()
        choice = input("Choose an option (1-3): ").strip()

        if choice == "1":
            choose_domain()
        elif choice == "2":
            show_current_domain()
        elif choice == "3":
            print("Exiting program.")
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProgram interrupted. Exiting cleanly. Goodbye!")
        exit(0)

