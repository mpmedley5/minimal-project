"""
Test script to verify domain-specific 'What do you know' response.
"""
import subprocess
import os

def run_chatbot_with_inputs(inputs, timeout=5):
    proc = subprocess.Popen(
        ["python", "cli_prototype_comptia_domains.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=os.getcwd()
    )
    out, err = proc.communicate(input="\n".join(inputs), timeout=timeout)
    return out, err

inputs = [
    "1",   # choose domain from main menu
    "1",   # select domain 1
    "what do you know",  # domain query
    "exit",
    "3"
]

out, err = run_chatbot_with_inputs(inputs, timeout=10)
print("--- STDOUT ---")
print(out)
print("--- STDERR ---")
print(err)

# Simple check
if "Here is what I know about CompTIA A+ Hardware" in out:
    print("✓ Domain data response found")
else:
    print("✗ Domain data response NOT found")
