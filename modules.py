import sys, os, re, datetime
from pathlib import Path
from collections import Counter

# Get current shell
parent_pid = os.getppid()
os.system(f"ps -p {parent_pid} -o comm= > shell")
with open("shell", "r") as file:
    shell = file.read().strip()
os.remove("shell")

# Locate the user's history file based on shell type (bash or zsh)
HIST_FILE = Path.home() / (".bash_history" if shell == "bash" else ".zsh_history")
if not HIST_FILE.exists():
    sys.exit("No history file found.")
with HIST_FILE.open('r', encoding='utf-8', errors='ignore') as hist:
    lines = hist.readlines()

commands, first_words, sudo_count, timestamps, days_of_week = [], [], 0, [], Counter()
args_by_cmd = {}

# Parse history file and collect useful data
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

bin_commands = set(os.listdir('/bin'))
excluded_commands = {".", "cd", "exit", "history", "exec"}
misspelled = [cmd for cmd in first_words if cmd not in bin_commands and cmd not in excluded_commands and not cmd.startswith(('.', '/', '~'))]
total_commands = len(first_words)

# Function to get color codes for terminal output
def getcolor(name, bold):
    colors = {"black": 30, "red": 31, "green": 32, "yellow": 33, "blue": 34,
              "magenta": 35, "cyan": 36, "white": 37}
    return f"\033[{colors.get(name, 37)}m" + ("\033[1m" if bold else "\033[22m")
def setheadercolor(color):
    global headercolor
    headercolor = getcolor(color, True)

# Function to print statistics (e.g., top commands or arguments used)
def print_stats(title, data, color1, color2, action):
    if not data:
        return
    print(f"\n{headercolor}{title}:")
    for i, (item, count) in enumerate(data, 1):
        print(f"{getcolor('blue', False)}{i}: {getcolor(color1, False)}{item} {getcolor('blue', False)}{action} {getcolor(color2, True)}{count} times")

# Function to display the most used arguments for a specific command
def mostargs(command, top_n, color):
    if command in args_by_cmd and args_by_cmd[command]:
        print_stats(f"Top {top_n} {command} arguments", Counter(args_by_cmd[command]).most_common(top_n), color, "green", "used")
def clear():
    os.system("clear")

def printtotal(color):
    print(f"{headercolor}Total commands: {getcolor(color, False)}{total_commands}")

def percentage(command, color):
    command_count = 0
    for line in lines:
        line = line.strip()
        if line.startswith(":"):
            # Handle timestamped lines
            parts = line.split(';', 1)
            if len(parts) > 1:
                cmd_line = parts[1].strip()
        else:
            # Handle non-timestamped lines
            cmd_line = line.strip()

        # Check if the command matches
        if cmd_line.startswith(command + " ") or cmd_line == command:
            command_count += 1

    if total_commands > 0:  # Prevent division by zero
        percentage_value = (command_count / total_commands) * 100
        print(f"\n{headercolor}Percentage of commands that are {command}: {getcolor(color, False)}{percentage_value:.2f}%")

# Convert timestamps to hours and store in 'times' list
times = [datetime.datetime.fromtimestamp(ts).hour for ts in timestamps]

# Function to display the time of the first command run
def firstcommand(color1, color2):
    if timestamps:
        first_command_time = datetime.datetime.fromtimestamp(timestamps[0]).strftime('%H:%M:%S on %m/%d/%y')
        print(f"\n{headercolor}First command run at {getcolor(color1, False)}{first_command_time}: {getcolor(color2, False)}{commands[0]}")
    else:
        print(f"\n{headercolor}First command: {getcolor(color2, False)}{commands[0]}")

def reset():
    print(getcolor("white", False))

# Function to display the number of commands run at each hour of the day
def hourly(color1, color2):
    if timestamps:
        hourly_counts = Counter(times)
        print(f"\n{headercolor}Number of commands run at each hour of the day:")
        for hour in range(12):
            left_hour, right_hour = hour, hour + 12
            left_count, right_count = hourly_counts[left_hour], hourly_counts[right_hour]
            space = " " * (10 - len(str(left_count)))
            print(f"{getcolor(color1, False)}{left_hour:02d} - {getcolor(color2, False)}{left_count}{space}"
                f"{getcolor(color1, False)}{right_hour:02d} - {getcolor(color2, False)}{right_count}")

def barchart(color1, color2):
    if timestamps:
        hourly_counts = Counter(times)
        print(f"\n{headercolor}Number of commands run at each hour of the day:")
        for i in len(height):
            for hour in range(12):
                height = hourly_counts[hour]
                # make a bar graph here that goes from the top down where height is a set varaible and all bars scale proportinally. should be same data from hourly but in bar graph format

def top_pings(top_n, color):
    if "ping" in args_by_cmd and args_by_cmd["ping"]:
        filtered_args = []
        for arg in args_by_cmd["ping"]:
            if re.search(r'\b\d{3}\b', arg):
                continue
            if '.' not in arg:
                continue
            filtered_args.append(arg)
        if filtered_args:
            print_stats(f"Top {top_n} pinged IPs", Counter(filtered_args).most_common(top_n), color, "green", "used")
        else:
            print(f"\n{headercolor}No valid {command} arguments found after filtering.")
def barchart(color1, color2):
    if timestamps:
        hourly_counts = Counter(times)
        max_count = max(hourly_counts.values()) if hourly_counts else 1
        print(f"\n{headercolor}Number of commands run at each hour of the day (bar chart):")
        for height in range(round(max_count/24), 0, -1):
            row = []
            for hour in range(24):
                if hourly_counts[hour]/24 >= height:
                    row.append(f"{getcolor(color2, True)}██")
                else:
                    row.append("  ")
            print(" ".join(row))
        print(f"{getcolor(color1, False)}" + " ".join(f"{hour:02d}" for hour in range(24)))
# Function to display the number of commands run on each day of the week
def byweekday(color1, color2):
    if timestamps:
        print(f"\n{headercolor}Number of commands run by day:")
        for day, count in days_of_week.items():
            print(f"{getcolor(color1, False)}{day}: {getcolor(color2, False)}{count}")
