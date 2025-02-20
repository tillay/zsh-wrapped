import sys, os, datetime, re
from pathlib import Path
from collections import Counter

shell = os.popen(f"ps -p {os.getppid()} -o comm=").read().strip()

HIST_FILE = Path.home() / (
    ".bash_history" if shell == "bash"
    else ".local/share/fish/fish_history" if shell == "fish"
    else ".zsh_history"
)

if not HIST_FILE.exists():
    sys.exit("No history file found.")

with HIST_FILE.open('r', encoding='utf-8', errors='ignore') as hist:
    lines = hist.readlines()

commands, first_words, timestamps, days_of_week = [], [], [], Counter()
args_by_cmd = {}

for line in lines:
    line = line.strip()
    if not line:
        continue

    if shell == "fish":
        if line.startswith("- cmd:"):
            cmd = line.split("cmd: ")[1].strip()
            split_cmd = cmd.split()
            first_word = split_cmd[0] if split_cmd else None
            args = " ".join(split_cmd[1:]) if len(split_cmd) > 1 else ""  # Ensure args is a string
        elif line.startswith("when:"):
            timestamp = int(line.split("when: ")[1].strip())
            timestamps.append(timestamp)
            days_of_week[datetime.datetime.fromtimestamp(timestamp).strftime('%A')] += 1
            continue
        else:
            continue
    else:
        if line.startswith(":"):
            parts = line.split(';', 1)
            if len(parts) > 1 and ':' in parts[0]:
                try:
                    timestamp = int(parts[0].split(':')[1])
                    timestamps.append(timestamp)
                    days_of_week[datetime.datetime.fromtimestamp(timestamp).strftime('%A')] += 1
                except ValueError:
                    continue
            command = parts[1] if len(parts) > 1 else ""
        else:
            command = line
        split_command = command.split()
        first_word = split_command[0] if split_command else None
        args = " ".join(split_command[1:]) if len(split_command) > 1 else ""  # Ensure args is a string

    if not first_word:
        continue

    first_words.append(first_word)
    commands.append(cmd if shell == "fish" else command)
    if first_word not in args_by_cmd:
        args_by_cmd[first_word] = []
    if args:
        args_by_cmd[first_word].append(args)

total_commands = len(first_words)

def getcolor(name, bold):
    colors = {"black": 30, "dark_red": 31, "green": 32, "dark_yellow": 33, "dark_blue": 34,
              "purple": 35, "teal": 36, "light_gray": 37, "dark_gray": 90, "red": 91,
              "lime": 92, "yellow": 93, "blue": 94, "magenta": 95, "cyan": 96, "white": 97}
    return f"\033[{colors.get(name, 37)}m" + ("\033[1m" if bold else "\033[22m")

def setheadercolor(color):
    global headercolor
    headercolor = getcolor(color, True)

def print_stats(title, data, color1, color2, action):
    if not data:
        return
    print(f"\n{headercolor}{title}:")
    for i, (item, count) in enumerate(data, 1):
        print(
            f"{getcolor('blue', False)}{i}: {getcolor(color1, False)}{item} {getcolor('blue', False)}{action} {getcolor(color2, True)}{count} {'times' if count > 1 else 'time'}")

def mostargs(command, top_n, color):
    if command in args_by_cmd and args_by_cmd[command]:
        print_stats(f"Top {top_n} {command} arguments", Counter(args_by_cmd[command]).most_common(top_n), color, "green", "used")

def topcmds(num, color1, color2):
    print_stats(f"Top {num} used commands", Counter(first_words).most_common(num), color1, color2, "used")

def clear():
    os.system("clear")

def printtotal(color):
    print(f"{headercolor}Total commands: {getcolor(color, False)}{total_commands}")

def percentage(command, color):
    command_count = sum(1 for cmd in commands if cmd.startswith(command + " ") or cmd == command)
    if total_commands > 0:
        percentage_value = (command_count / total_commands) * 100
        print(f"\n{headercolor}Percentage of commands that are {command}: {getcolor(color, False)}{percentage_value:.2f}%")

times = [datetime.datetime.fromtimestamp(ts).hour for ts in timestamps]

def firstcommand(color1, color2):
    if timestamps:
        first_command_time = datetime.datetime.fromtimestamp(timestamps[0]).strftime('%H:%M:%S on %m/%d/%y')
        print(f"\n{headercolor}First command run at {getcolor(color1, False)}{first_command_time}: {getcolor(color2, False)}{commands[0]}")
    else:
        print(f"\n{headercolor}First command: {getcolor(color2, False)}{commands[0]}")

def reset():
    print(getcolor("white", False))

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

def top_pings(top_n, color):
    if "ping" in args_by_cmd and args_by_cmd["ping"]:
        filtered_args = [arg for arg in args_by_cmd["ping"] if re.search(r'\b\d{3}\b', arg) is None and '.' in arg]
        if filtered_args:
            print_stats(f"Top {top_n} pinged IPs", Counter(filtered_args).most_common(top_n), color, "green", "used")

def barchart(color1, color2):
    if timestamps:
        hourly_counts = Counter(times)
        max_count = max(hourly_counts.values()) if hourly_counts else 1
        scalar = max_count / 18
        print(f"\n{headercolor}Number of commands run at each hour of the day (bar chart):\n")
        for height in range(round(max_count / scalar), 0, -1):
            row = []
            for hour in range(24):
                if hourly_counts[hour] / scalar >= height:
                    row.append(f"{getcolor(color2, True)}██")
                elif hourly_counts[hour] / scalar >= height - 0.25:
                    row.append(f"{getcolor(color2, True)}▆▆")
                elif hourly_counts[hour] / scalar >= height - 0.5:
                    row.append(f"{getcolor(color2, True)}▄▄")
                elif hourly_counts[hour] / scalar >= height - 0.75:
                    row.append(f"{getcolor(color2, True)}▂▂")
                else:
                    row.append("  ")
            print(" ".join(row))
        print(f"{getcolor(color1, False)}" + " ".join(f"{hour:02d}" for hour in range(24)))

def daychart(color1, color2):
    if timestamps:
        daily_counts = days_of_week
        max_count = max(daily_counts.values()) if daily_counts else 1
        scalar = max_count / 10
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        print(f"\n{headercolor}Number of commands run on each day (bar chart):\n")
        for height in range(round(max_count / scalar), 0, -1):
            row = []
            for day in days:
                if daily_counts.get(day, 0) / scalar >= height:
                    row.append(f"{getcolor(color2, True)}███████")
                elif daily_counts.get(day, 0) / scalar >= height - 0.25:
                    row.append(f"{getcolor(color2, True)}▆▆▆▆▆▆▆")
                elif daily_counts.get(day, 0) / scalar >= height - 0.5:
                    row.append(f"{getcolor(color2, True)}▄▄▄▄▄▄▄")
                elif daily_counts.get(day, 0) / scalar >= height - 0.75:
                    row.append(f"{getcolor(color2, True)}▂▂▂▂▂▂▂")
                else:
                    row.append("       ")
            print(" ".join(row))
        print(f"{getcolor(color1, False)}" + " ".join(f"  {day[:3]}  " for day in days))

def byweekday(color1, color2):
    if timestamps:
        print(f"\n{headercolor}Number of commands run by day:")
        for day, count in days_of_week.items():
            print(f"{getcolor(color1, False)}{day}: {getcolor(color2, False)}{count}")
