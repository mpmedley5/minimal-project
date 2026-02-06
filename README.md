# CompTIA Learning Chatbot - CLI Prototype

A command-line chatbot application designed to help Information Technology students learn CompTIA certification course content. Students can select a domain, ask questions, and save Q&A interactions for future reference.

## Project Overview

**Course**: IT Education Technology (TEIT)  
**Tool Name**: Newman - AI Teaching Assistant  
**Purpose**: Support students in learning CompTIA certification objectives through interactive Q&A conversations.

## Features

### Core Functionality
- **Domain Selection**: Students choose from 7 CompTIA domains (A+ Hardware, A+ Software, Network+, Security+, Linux+, Pentest+, CySA+)
- **Interactive Chat**: Ask questions about selected domain content
- **Save Conversations**: Store Q&A pairs for later review
- **List Saved Q&As**: View last 10 saved conversations with timestamps
- **Persistent Storage**: All conversations saved to JSON file across multiple sessions

### User Commands (in Chat Mode)
- Type a question → Newman responds
- `save` → Save last question/answer pair
- `list` → Display last 10 saved Q&A pairs
- `exit` → Return to main menu

## Data Model

### Q&A Conversation Record
Each saved conversation is stored as a Python dictionary with the following fields:

```python
{
    "id": "unique-uuid-string",           # Unique identifier for this record
    "question": "student question text",   # The question asked by the student
    "response": "newman response text",    # The AI-generated response
    "timestamp": "2026-02-06T13:33:46",   # ISO format timestamp when saved
    "domain": "CompTIA A+ Hardware"        # Domain this conversation belongs to
}
```

### Master Data Structure
All conversations are stored as a list of dictionaries:
```python
APP_STATE["conversations"] = [
    {record1},
    {record2},
    ...
]
```

## File Structure

```
.
├── cli_prototype_comptia_domains.py  # Main chatbot application
├── qa_conversations.json              # Persistent storage (auto-created)
├── test_persistence.py                # Test suite for save/load functionality
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── pyproject.toml                     # Project configuration
└── .gitignore                         # Git ignore rules
```

## Installation

### Prerequisites
- Python 3.8+
- Virtual environment (recommended)

### Setup

1. Clone or download the project
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   ```
3. Activate the virtual environment:
   - **Windows PowerShell**: `.\.venv\Scripts\Activate.ps1`
   - **Windows CMD**: `.venv\Scripts\activate.bat`
   - **macOS/Linux**: `source .venv/bin/activate`

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the chatbot:
```bash
python cli_prototype_comptia_domains.py
```

### Example Workflow

1. Program starts with main menu
2. Select option `1` to choose a domain
3. Pick a domain (e.g., `1` for CompTIA A+ Hardware)
4. Type a question: `What is a CPU?`
5. Newman responds with acknowledgment
6. Type `save` to save this Q&A pair
7. Type `list` to view all saved Q&A pairs (up to 10 most recent)
8. Type `exit` to return to main menu
9. Select option `3` to exit the program

## Testing

Run the persistence test to verify save/load functionality:
```bash
python test_persistence.py
```

This test:
- Creates a session and saves a Q&A
- Closes and restarts the program
- Verifies the previous Q&A was loaded
- Adds a new Q&A
- Confirms both records exist in JSON file

## Development Notes

### Chunk 1: Core CLI
- Domain selection menu
- Interactive chat prompts
- Basic save/list commands

### Chunk 2: Persistent Storage & Structured Data
- Implemented JSON file storage
- Structured Q&A records with unique IDs and timestamps
- Automatic loading of conversations on startup
- All conversations persist across program sessions

## Structured Data Compliance

This project fully implements the professor's technical challenge requirements:

1. **Dictionary Representation**: Each Q&A is a single Python dictionary
2. **Schema Fields**: Keys correspond to defined fields: `id`, `question`, `response`, `timestamp`, `domain`
3. **Master List**: All dictionaries stored in `APP_STATE["conversations"]` list
4. **List Iteration**: The `list` command iterates through the list of dictionaries
5. **Unchanged User Experience**: External behavior identical to previous version

## Future Enhancements

- Integration with real AI/LLM for responses
- Search functionality across saved conversations
- Export conversations to PDF
- User authentication and profiles
- Database backend (replace JSON)
- Web interface

## Requirements

See `requirements.txt` for dependencies (currently minimal - uses only standard library).

## License

Educational use - CompTIA Learning Tool
