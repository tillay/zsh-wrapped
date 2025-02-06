import sys, os, datetime, re
from pathlib import Path
from collections import Counter

def getcolor(name, bold):
    colors = {"black": 30, "dark_red": 31, "green": 32, "dark_yellow": 33, "dark_blue": 34,
              "purple": 35, "teal": 36, "light_gray": 37, "dark_gray": 90, "red": 91,
              "lime": 92, "yellow": 93, "blue": 94, "magenta": 95, "cyan": 96, "white": 97}
    return f"\033[{colors.get(name, 37)}m" + ("\033[1m" if bold else "\033[22m")

def print_stats(title, data, color1, color2, action):
    print(f"\n{getcolor('teal', True)}{title}:")
    for i, (item, count) in enumerate(data, 1):
        print(f"{getcolor('blue', False)}{i}: {getcolor(color1, False)}{item} {getcolor('blue', False)}{action} {getcolor(color2, True)}{count} {getcolor('blue', False)}times")

def mostargs(command, top_n, color):
    if command in args_by_cmd:
        print_stats(f"Top {top_n} {command} arguments", Counter(args_by_cmd[command]).most_common(top_n), color, "lime", "used")

def mostpinged(top_n):
    filtered_ips = [ip for ip in pinged_ips if ('.' in ip and not re.search(r'\b\d{3}\b', ip))]
    print_stats(f"Top {top_n} pinged addresses", Counter(filtered_ips).most_common(top_n), "magenta", "lime", "pinged")

HISTORY_FILE = Path.home() / ".zsh_history"
if not HISTORY_FILE.exists():
    print("No history file found.")
    sys.exit(1)

with HISTORY_FILE.open('r', encoding='utf-8', errors='ignore') as hist:
    lines = hist.readlines()

commands, timestamps, first_words, sudo_count, pinged_ips = [], [], [], 0, []
args_by_cmd = {}

days_of_week = Counter()

for line in lines:
    parts = line.strip().split(';', 1)
    if len(parts) == 2 and ':' in parts[0]:
        try:
            timestamp = int(parts[0].split(':')[1])
            timestamps.append(timestamp)
            command = parts[1].strip()
            commands.append(command)
            split_cmd = command.split()
            if not split_cmd:
                continue
            first_word, args = split_cmd[0], " ".join(split_cmd[1:])
            first_words.append(first_word)
            if first_word not in args_by_cmd:
                args_by_cmd[first_word] = []
            if args:
                args_by_cmd[first_word].append(args)
            if first_word == "sudo":
                sudo_count += 1
            if first_word == "ping" and len(split_cmd) > 1:
                pinged_ips.append(split_cmd[1])
            day_of_week = datetime.datetime.fromtimestamp(timestamp).strftime('%A')
            days_of_week[day_of_week] += 1
        except ValueError:
            continue

os.system("clear")
bin_commands = set(os.listdir('/bin'))
excluded_commands = {".", "cd", "while", "exit", "history", "exec"}
misspelled = [cmd for cmd in first_words if cmd not in bin_commands and cmd not in excluded_commands and not cmd.startswith('.')]

print(f"{getcolor('teal', True)}Total commands: {getcolor('lime', True)}{len(commands)}")

print_stats("Top 10 used commands", Counter(first_words).most_common(10), "magenta", "lime", "used")

print_stats("Top 10 misspelled commands", Counter(misspelled).most_common(20), "red", "lime", "used")

mostargs("git", 5, "yellow")
mostargs("cd", 5, "red")
mostargs("rm", 12, "green")
mostpinged(10)

print(f"\n{getcolor('teal', True)}Percentage of commands run with sudo: {getcolor('red', False)}{(sudo_count / len(commands) * 100 if commands else 0):.2f}%")

if commands:
    first_command_time = datetime.datetime.fromtimestamp(timestamps[0]).strftime('%H:%M:%S on %m/%d/%y')
    print(f"\n{getcolor('teal', True)}First command run at {getcolor('yellow', False)}{first_command_time}: {getcolor('magenta', True)}{commands[0]}\n")

    times = [datetime.datetime.fromtimestamp(ts).hour for ts in timestamps]
    time_ranges = [(22, 4, "night"), (4, 12, "morning"), (12, 22, "afternoon")]
    total_time_count = len(times)

    for start, end, label in time_ranges:
        count = sum(1 for t in times if start <= t < end or (start > end and (t >= start or t < end)))
        print(f"{getcolor('blue', False)}You run commands in the {label} {getcolor('red', True)}{(count / total_time_count * 100):.2f}%{getcolor('blue', False)} of the time.")

    hourly_counts = Counter(times)
    print(f"\n{getcolor('teal', True)}Number of commands run at each hour of the day:")
    for hour in range(12):
        left_hour, right_hour = hour, hour + 12
        left_count, right_count = hourly_counts[left_hour], hourly_counts[right_hour]
        space = " " * (10 - len(str(left_count)))
        print(f"{getcolor('blue', False)}{left_hour:02d} - {getcolor('lime', False)}{left_count}{space}"
              f"{getcolor('blue', False)}{right_hour:02d} - {getcolor('lime', False)}{right_count}")

    print(f"\n{getcolor('teal', True)}Number of commands run each day:")
    for day, count in days_of_week.items():
        print(f"{getcolor('magenta', False)}{day}: {getcolor('dark_blue', False)}{count}")
