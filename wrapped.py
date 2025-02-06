import sys
import os
import datetime
from pathlib import Path
from collections import Counter
import re

def getcolor(color_name, bold):
    colors = [
        ("black", "\033[30m"), ("dark_red", "\033[31m"), ("green", "\033[32m"),
        ("dark_yellow", "\033[33m"), ("dark_blue", "\033[34m"), ("purple", "\033[35m"),
        ("teal", "\033[36m"), ("light_gray", "\033[37m"),
        ("dark_gray", "\033[90m"), ("red", "\033[91m"), ("lime", "\033[92m"),
        ("yellow", "\033[93m"), ("blue", "\033[94m"), ("magenta", "\033[95m"),
        ("cyan", "\033[96m"), ("white", "\033[97m"),
    ]
    for name, escape_sequence in colors:
        if name == color_name:
            return escape_sequence + ("\033[1m" if bold else "\033[22m")
    return None

HISTORY_FILE = Path(os.path.expanduser("~/.zsh_history"))
if not HISTORY_FILE.is_file():
    print("No history file found.")
    sys.exit(1)

with open(HISTORY_FILE, 'r', encoding='utf-8', errors='ignore') as hist:
    lines = hist.readlines()

commands = []
timestamps = []
ping_ips = []
sudo_count = 0

for line in lines:
    parts = line.strip().split(';', 1)
    if len(parts) == 2:
        timestamp_part = parts[0].split(':')
        if len(timestamp_part) > 1:
            try:
                timestamp = int(timestamp_part[1])
                timestamps.append(timestamp)
                command = parts[1].strip()
                commands.append(command)

                if command.startswith("ping"):
                    ping_parts = command.split()
                    if len(ping_parts) > 1:
                        ip = ping_parts[1]
                        if not re.match(r'^\d{3}\.\d+\.\d+\.\d+$', ip):
                            ping_ips.append(ip)

                if command.startswith("sudo"):
                    sudo_count += 1
            except ValueError:
                continue

first_words = [cmd.split()[0] for cmd in commands]

bin_commands = set(os.listdir('/bin'))
excluded_commands = {".", "cd", "while", "exit", "history"}
misspelled = [cmd for cmd in first_words if cmd not in bin_commands and cmd not in excluded_commands and not cmd.startswith('.')]

most_common_commands = Counter(first_words).most_common(10)
most_common_misspelled = Counter(misspelled).most_common(10)
most_common_pinged_ips = Counter(ping_ips).most_common(10)

total_count = len(commands)
sudo_percentage = (sudo_count / total_count) * 100 if total_count > 0 else 0

print(f"\n{getcolor('teal', False)}Total commands: {getcolor('lime', True)}{total_count}")
print(f"\n{getcolor('teal', False)}Top 10 used commands:")
for i, (command, count) in enumerate(most_common_commands, start=1):
    print(f"{getcolor('blue', False)}{i}: {getcolor('red', False)}{command} {getcolor('blue', False)}used {getcolor('lime', True)}{count} {getcolor('blue', False)}times")

print(f"\n{getcolor('teal', False)}Top 10 misspelled commands:")
for i, (command, count) in enumerate(most_common_misspelled, start=1):
    print(f"{getcolor('blue', False)}{i}: {getcolor('red', False)}{command} {getcolor('blue', False)}used {getcolor('lime', True)}{count} {getcolor('blue', False)}times")

print(f"\n{getcolor('teal', False)}Top 10 most pinged IPs:")
for i, (ip, count) in enumerate(most_common_pinged_ips, start=1):
    print(f"{getcolor('blue', False)}{i}: {getcolor('red', False)}{ip} {getcolor('blue', False)}pinged {getcolor('lime', True)}{count} {getcolor('blue', False)}times")

print(f"\n{getcolor('teal', False)}Percentage of commands run with sudo: {getcolor('red', True)}{sudo_percentage:.2f}%")

if total_count > 0:
    first_command_time = datetime.datetime.fromtimestamp(timestamps[0]).strftime('%Y-%m-%d %H:%M:%S')
    print(f"\n{getcolor('teal', False)}First command run at {getcolor('lime', True)}{first_command_time}: {getcolor('red', True)}{commands[0]}")

    night_count = sum(1 for ts in timestamps if datetime.datetime.fromtimestamp(ts).hour in range(22, 24)) + sum(1 for ts in timestamps if datetime.datetime.fromtimestamp(ts).hour in range(0, 4))
    morning_count = sum(1 for ts in timestamps if datetime.datetime.fromtimestamp(ts).hour in range(4, 12))
    afternoon_count = sum(1 for ts in timestamps if datetime.datetime.fromtimestamp(ts).hour in range(12, 22))

    total_time_count = night_count + morning_count + afternoon_count

    if total_time_count > 0:
        night_percentage = (night_count / total_time_count) * 100
        morning_percentage = (morning_count / total_time_count) * 100
        afternoon_percentage = (afternoon_count / total_time_count) * 100

        print(f"\n{getcolor('blue', False)}You make commands at night {getcolor('red', True)}{night_percentage:.2f}%{getcolor('blue', False)} of the time.")
        print(f"You make commands in the morning {getcolor('red', True)}{morning_percentage:.2f}%{getcolor('blue', False)} of the time.")
        print(f"You make commands in the afternoon {getcolor('red', True)}{afternoon_percentage:.2f}%{getcolor('blue', False)} of the time.")
