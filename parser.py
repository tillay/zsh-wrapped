import sys, os, datetime
from pathlib import Path
from collections import Counter

# Get current shell using dark magic (works 90% of the time)
shell = os.popen(f"ps -p {os.getppid()} -o comm=").read().strip()

# Locate the user's history file based on shell type using a lookup table
HIST_FILE = Path.home() / (
    ".zsh_history" if shell == "zsh"
    else ".local/share/fish/fish_history" if shell == "fish"
    else f".{shell}_history" # Assume that the history for jank shells is ~/.<shell>_history
)
# Exit with an error if that expected history file does not exist.
if not HIST_FILE.exists():
    sys.exit(f"No history file found. Detected shell is {shell}")

# Read the history file and store its contents
with HIST_FILE.open('r', encoding='utf-8', errors='ignore') as hist:
    lines = hist.readlines()

# Create big array of dictionaries of the command and the timestamp
history_entries = []

for line in lines:
    # Random redundancy cause it broke if I didn't have it
    if not (line := line.strip()):
        continue

    # Array entry outline
    entry = {'cmd': None, 'timestamp': None}

    if shell == "fish": # Parse fish history
        if line.startswith("- cmd:"):
            entry['cmd'] = line.split("cmd: ")[1].strip()
        elif line.startswith("when:") and history_entries:
            history_entries[-1]['timestamp'] = int(line.split("when: ")[1].strip())

    elif shell == "zsh": # Parse zsh history
            parts = line.split(';', 1)
            if len(parts) > 1 and ':' in parts[0]:
                try:
                    entry['timestamp'] = int(parts[0].split(':')[1])
                except ValueError:
                    pass
            entry['cmd'] = parts[1].strip() if len(parts) > 1 else ""

    else: # Parse other histories (probably bash)
        entry['cmd'] = line.strip()

    if entry['cmd']: # Append that info it everything worked
        history_entries.append(entry)

# More refined arrays for modules to use
# I'm too lazy to try removing the redundancy and make it still work
commands = [entry['cmd'] for entry in history_entries]
binaries = [cmd.split()[0] if cmd else None for cmd in commands]
timestamps = [entry['timestamp'] for entry in history_entries if entry['timestamp'] is not None]
hours = [datetime.datetime.fromtimestamp(ts).hour for ts in timestamps]
days_of_week = Counter(datetime.datetime.fromtimestamp(ts).strftime('%A') for ts in timestamps)

args_by_cmd = {}
for e in history_entries:
    if (p := e['cmd'].split() if e['cmd'] else []):
        args_by_cmd.setdefault(p[0], []).append(" ".join(p[1:])) if len(p) > 1 else args_by_cmd.setdefault(p[0], [])
