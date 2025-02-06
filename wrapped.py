import sys, os, re, datetime
from pathlib import Path
from collections import Counter

def getcolor(name, bold):
    colors = {"black": 30, "red": 31, "green": 32, "yellow": 33, "blue": 34,
              "magenta": 35, "cyan": 36, "white": 37, "gray": 90}
    return f"\033[{colors.get(name, 37)}m" + ("\033[1m" if bold else "\033[22m")

def print_stats(title, data, color1, color2, action):
    if not data:
        return
    print(f"\n{getcolor('cyan', True)}{title}:")
    for i, (item, count) in enumerate(data, 1):
        print(f"{getcolor('blue', False)}{i}: {getcolor(color1, False)}{item} {getcolor('blue', False)}{action} {getcolor(color2, True)}{count} times")

def mostargs(command, top_n, color):
    if command in args_by_cmd and args_by_cmd[command]:
        print_stats(f"Top {top_n} {command} arguments", Counter(args_by_cmd[command]).most_common(top_n), color, "green", "used")

HIST_FILE = Path.home() / (".zsh_history" if Path.home().joinpath(".zsh_history").exists() else ".bash_history")
if not HIST_FILE.exists():
    sys.exit("No history file found.")

with HIST_FILE.open('r', encoding='utf-8', errors='ignore') as hist:
    lines = hist.readlines()

commands, first_words, sudo_count, timestamps, days_of_week = [], [], 0, [], Counter()
args_by_cmd = {}

for line in lines:
    line = line.strip()
    if not line:
        continue
    if line.startswith(":"):
        parts = line.split(';', 1)
        if len(parts) > 1 and ':' in parts[0]:
            try:
                timestamp = int(parts[0].split(':')[1])
                timestamps.append(timestamp)
                day_of_week = datetime.datetime.fromtimestamp(timestamp).strftime('%A')
                days_of_week[day_of_week] += 1
            except ValueError:
                continue
        command = parts[1] if len(parts) > 1 else ""
    else:
        command = line

    split_cmd = command.split()
    if not split_cmd:
        continue
    first_word, args = split_cmd[0], " ".join(split_cmd[1:])
    first_words.append(first_word)
    commands.append(command)
    if first_word not in args_by_cmd:
        args_by_cmd[first_word] = []
    if args:
        args_by_cmd[first_word].append(args)
    if first_word == "sudo":
        sudo_count += 1

os.system("clear")
bin_commands = set(os.listdir('/bin'))
excluded_commands = {".", "cd", "exit", "history", "exec"}
misspelled = [cmd for cmd in first_words if cmd not in bin_commands and cmd not in excluded_commands and not cmd.startswith(('.', '/', '~'))]

total_commands = len(first_words)
print(f"{getcolor('cyan', True)}Total commands: {getcolor('green', True)}{total_commands}")

print_stats("Top 10 used commands", Counter(first_words).most_common(10), "magenta", "green", "used")
print_stats("Top 10 misspelled commands", Counter(misspelled).most_common(10), "red", "green", "run")

mostargs("git", 5, "yellow")
mostargs("cd", 5, "red")
mostargs("rm", 12, "green")

if total_commands > 0:
    print(f"\n{getcolor('cyan', True)}Percentage of commands run with sudo: {getcolor('red', False)}{(sudo_count / total_commands * 100):.2f}%")

    if timestamps:
        first_command_time = datetime.datetime.fromtimestamp(timestamps[0]).strftime('%H:%M:%S on %m/%d/%y')
        print(f"\n{getcolor('cyan', True)}First command run at {getcolor('yellow', False)}{first_command_time}: {getcolor('magenta', True)}{commands[0]}")

        times = [datetime.datetime.fromtimestamp(ts).hour for ts in timestamps]
        time_ranges = [(22, 4, "night"), (4, 12, "morning"), (12, 22, "afternoon")]
        total_time_count = len(times)

        for start, end, label in time_ranges:
            count = sum(1 for t in times if start <= t < end or (start > end and (t >= start or t < end)))
            print(f"{getcolor('blue', False)}You run commands in the {label} {getcolor('red', True)}{(count / total_time_count * 100):.2f}%{getcolor('blue', False)} of the time.")

        hourly_counts = Counter(times)
        print(f"\n{getcolor('cyan', True)}Number of commands run at each hour of the day:")
        for hour in range(12):
            left_hour, right_hour = hour, hour + 12
            left_count, right_count = hourly_counts[left_hour], hourly_counts[right_hour]
            space = " " * (10 - len(str(left_count)))
            print(f"{getcolor('blue', False)}{left_hour:02d} - {getcolor('green', False)}{left_count}{space}"
                  f"{getcolor('blue', False)}{right_hour:02d} - {getcolor('green', False)}{right_count}")

        print(f"\n{getcolor('cyan', True)}Number of commands run each day:")
        for day, count in days_of_week.items():
            print(f"{getcolor('magenta', False)}{day}: {getcolor('blue', False)}{count}")
