"""
Test script to verify persistent storage of Q&A conversations.
Tests save/load functionality across multiple program sessions.
"""

import json
import subprocess
import os
import time

QA_FILE = "qa_conversations.json"

def run_chatbot_session(inputs):
    """Run chatbot with provided inputs and return output."""
    process = subprocess.Popen(
        ["python", "cli_prototype_comptia_domains.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=os.getcwd()
    )
    
    output, error = process.communicate(input="\n".join(inputs), timeout=10)
    return output, error

def check_json_file():
    """Check and display contents of qa_conversations.json."""
    if os.path.exists(QA_FILE):
        with open(QA_FILE, 'r') as f:
            data = json.load(f)
            return data
    return []

print("=" * 70)
print("CHUNK 2: PERSISTENT STORAGE TEST")
print("=" * 70)

# Test 1: First session - select domain, ask question, save it
print("\n[TEST 1] First session - Save Q&A to domain 1")
print("-" * 70)
inputs_session1 = ["1", "1", "What is CPU?", "save", "exit", "3"]
output1, error1 = run_chatbot_session(inputs_session1)
print("Session 1 completed.")

# Check JSON after first session
conversations_after_1 = check_json_file()
print(f"\nConversations saved: {len(conversations_after_1)}")
if conversations_after_1:
    for i, conv in enumerate(conversations_after_1, 1):
        print(f"\n  Record {i}:")
        print(f"    ID: {conv['id']}")
        print(f"    Question: {conv['question']}")
        print(f"    Domain: {conv['domain']}")
        print(f"    Timestamp: {conv['timestamp']}")

# Test 2: Second session - verify previous data loads, add another Q&A
print("\n" + "=" * 70)
print("[TEST 2] Second session - Verify reload + save new Q&A")
print("-" * 70)
time.sleep(1)
inputs_session2 = ["1", "1", "What is RAM?", "save", "list", "exit", "3"]
output2, error2 = run_chatbot_session(inputs_session2)
print("Session 2 completed.")

# Check JSON after second session
conversations_after_2 = check_json_file()
print(f"\nConversations saved: {len(conversations_after_2)}")
if conversations_after_2:
    for i, conv in enumerate(conversations_after_2, 1):
        print(f"\n  Record {i}:")
        print(f"    ID: {conv['id']}")
        print(f"    Question: {conv['question']}")
        print(f"    Domain: {conv['domain']}")

# Verification
print("\n" + "=" * 70)
print("VERIFICATION RESULTS")
print("=" * 70)

if len(conversations_after_1) == 1:
    print("✓ First save created 1 record in JSON")
else:
    print(f"✗ Expected 1 record after first session, got {len(conversations_after_1)}")

if len(conversations_after_2) == 2:
    print("✓ Second session loaded previous record + added new one (2 total)")
else:
    print(f"✗ Expected 2 records after second session, got {len(conversations_after_2)}")

# Verify structure
if conversations_after_2:
    required_fields = ["id", "question", "response", "timestamp", "domain"]
    record = conversations_after_2[0]
    missing = [f for f in required_fields if f not in record]
    if not missing:
        print("✓ All required fields present in saved records")
    else:
        print(f"✗ Missing fields: {missing}")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
