# This file is a duplicate of the original CLI prototype (cli_prototype_comptia_domains.py)
# renamed to comptia_domains_webapp.py as requested.  The contents are identical so
# that the original functionality (domain selection, persistence, etc.) is retained.
#
# You may eventually modify this copy to incorporate web-specific logic or to act as
# the entry point for the combined CLI/web project.  For now it remains a faithful
# copy of the previous prototype.

import json
import os
from datetime import datetime
from uuid import uuid4

# File path for persistent Q&A storage
QA_FILE = "qa_conversations.json"

# File path for per-domain sample data
DOMAIN_DATA_FILE = "domain_data.json"

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
        "CompTIA SecAI+",
   ],
    "current_domain": None,
    "conversations": [],
    "domain_data": {}
}


def load_conversations() -> None:
    """Load conversations from JSON file into APP_STATE."""
    if os.path.exists(QA_FILE):
        try:
            with open(QA_FILE, 'r') as f:
                APP_STATE["conversations"] = json.load(f)
        except (json.JSONDecodeError, IOError):
            APP_STATE["conversations"] = []
    else:
        APP_STATE["conversations"] = []


def save_conversations() -> None:
    """Write current APP_STATE conversations to disk."""
    try:
        with open(QA_FILE, 'w') as f:
            json.dump(APP_STATE["conversations"], f, indent=2)
    except IOError:
        pass


def load_domain_data() -> None:
    """Load domain descriptions from JSON file into APP_STATE."""
    if os.path.exists(DOMAIN_DATA_FILE):
        try:
            with open(DOMAIN_DATA_FILE, 'r') as f:
                APP_STATE["domain_data"] = json.load(f)
        except (json.JSONDecodeError, IOError):
            APP_STATE["domain_data"] = {}
    else:
        APP_STATE["domain_data"] = {}


def select_domain() -> None:
    """Display domains and allow the user to choose one."""
    print("\nAvailable domains:")
    for idx, d in enumerate(APP_STATE["domains"], start=1):
        print(f"{idx}) {d}")

    choice = input("\nSelect a domain by number: ")
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(APP_STATE["domains"]):
            APP_STATE["current_domain"] = APP_STATE["domains"][idx]
            print(f"Current domain set to: {APP_STATE['current_domain']}")
        else:
            print("Invalid selection.")
    except ValueError:
        print("Invalid input; please enter a number.")


def show_current_domain() -> None:
    """Print the currently selected domain."""
    cd = APP_STATE.get("current_domain")
    if cd:
        print(f"Currently studying: {cd}")
    else:
        print("No domain selected.")


def main() -> None:
    """Main program loop."""
    load_conversations()
    load_domain_data()

    print("Command-Line Application Prototype - Domain Selector")
    print("==============================================================")
    print("Welcome to the Information Technology student learning chatbot")
    print("Hello, I am Newman, your AI teaching assistant")
    print("I am here to help you learn course content for TEIT courses")

    while True:
        print("\nYou can ask me questions about specific CompTIA course content")
        print("1) Choose a domain")
        print("2) Show current domain")
        print("3) Exit program")
        choice = input("Choose an option (1-3):")

        if choice == '1':
            select_domain()
        elif choice == '2':
            show_current_domain()
        elif choice == '3':
            print("Program interrupted. Exiting cleanly. Goodbye!")
            break
        else:
            print("Invalid option.")


if __name__ == "__main__":
    main()
