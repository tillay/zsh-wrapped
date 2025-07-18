import sys, os, datetime
from pathlib import Path
from collections import Counter

# Get current shell using dark magic (works 90% of the time)
# The .lstrip('-') is added to remove the leading hyphen from login shells (e.g., "-zsh" -> "zsh")
shell = os.popen(f"ps -p {os.getppid()} -o comm=").read().strip().lstrip('-')

# Locate the user's history file based on shell type using a lookup table
HIST_FILE = Path.home() / (
    ".zsh_history" if shell == "zsh"
    else ".local/share/fish/fish_history" if shell == "fish"
    else f".{shell}_history" # Assume that the history for jank shells is ~/.<shell>_history
)
# Exit with an error if that expected history file does not exist.
if not HIST_FILE.exists():
    # Provide a more informative error message
    sys.exit(f"Error: History file not found at '{HIST_FILE}'. Detected shell is '{shell}'.")

# Read the history file and store its contents
with HIST_FILE.open('r', encoding='utf-8', errors='ignore') as hist:
    lines = hist.readlines()

# Create big array of dictionaries of the command and the timestamp
history_entries = []

for line in lines:
    # Use walrus operator correctly and skip empty lines
    if not (line := line.strip()):
        continue

    # Array entry outline
    entry = {'cmd': None, 'timestamp': None}

    if shell == "fish": # Parse fish history
        if line.startswith("- cmd:"):
            entry['cmd'] = line.split("cmd: ", 1)[1].strip()
        elif line.startswith("when:") and history_entries:
            # Ensure the last entry doesn't already have a timestamp
            if history_entries[-1]['timestamp'] is None:
                history_entries[-1]['timestamp'] = int(line.split("when: ", 1)[1].strip())
        # If the line is a command, add it to history_entries immediately
        if entry['cmd']:
            history_entries.append(entry)

    elif shell == "zsh": # Parse zsh history
        # ZSH extended history format: : <timestamp>:<duration>;<command>
        if line.startswith(':') and ';' in line:
            parts = line.split(';', 1)
            try:
                # Extract timestamp, ignoring duration if present
                entry['timestamp'] = int(parts[0].split(':')[1].strip())
                entry['cmd'] = parts[1].strip()
            except (ValueError, IndexError):
                # If parsing timestamp fails, treat the whole line as a command
                entry['cmd'] = line
        else:
            # Fallback for simple history format
            entry['cmd'] = line

        if entry['cmd']: # Append that info if everything worked
            history_entries.append(entry)

    else: # Parse other histories (probably bash)
        entry['cmd'] = line.strip()
        if entry['cmd']:
            history_entries.append(entry)


# --- Analysis Section ---

# More refined arrays for modules to use
commands = [entry['cmd'] for entry in history_entries if entry.get('cmd')]
binaries = [cmd.split()[0] for cmd in commands if cmd]
timestamps = [entry['timestamp'] for entry in history_entries if entry.get('timestamp')]

# Handle cases where timestamps might not be available for all entries
hours = [datetime.datetime.fromtimestamp(ts).hour for ts in timestamps]
days_of_week = Counter(datetime.datetime.fromtimestamp(ts).strftime('%A') for ts in timestamps)

args_by_cmd = {}
for cmd_str in commands:
    parts = cmd_str.split()
    if not parts:
        continue
    binary = parts[0]
    # Ensure the key exists before appending
    if binary not in args_by_cmd:
        args_by_cmd[binary] = []
    # Append arguments if they exist
    if len(parts) > 1:
        args_by_cmd[binary].append(" ".join(parts[1:]))

# Example of how to see the output
# print(f"Found {len(commands)} commands.")
# print(f"Most common command: {Counter(binaries).most_common(1)}")
# print(f"Most active day: {days_of_week.most_common(1)}")