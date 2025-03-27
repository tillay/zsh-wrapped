import sys, os, datetime, re, subprocess
from pathlib import Path
from collections import Counter

# Get current shell using dark magic (works 90% of the time)
shell = os.popen(f"ps -p {os.getppid()} -o comm=").read().strip()

# Locate the user's history file based on shell type using a lookup table
HIST_FILE = Path.home() / (
    ".bash_history" if shell == "bash"
    else ".local/share/fish/fish_history" if shell == "fish"
    else ".zsh_history"
)
# Exit with an error if that expected history file does not exist.
if not HIST_FILE.exists():
    sys.exit(f"No history file found. Expected to find {HIST_FILE} because detected shell is {shell}")

# Read the history file and store its contents
# Returns the array lines - this is not helpful by itself and is parsed in the magic box below
with HIST_FILE.open('r', encoding='utf-8', errors='ignore') as hist:
    lines = hist.readlines()

# Below is a magic box of code that I hardly understand that parses all the command history
# It takes the shell figured out earlier and parses the history file based on that shell to get some arrays
# I wrote this box while high at 2am. I have no memory of writing it, but it works, so I am not touching it
# explanation of returned arrays below

# MAGIC BOX STARTS HERE
commands, first_words, timestamps, days_of_week, args_by_cmd = [], [], [], Counter(), {}
for line in lines:
    if not (line := line.strip()): continue
    if shell == "fish":
        if line.startswith("- cmd:"):
            cmd = line.split("cmd: ")[1].strip()
            first_word, *args = cmd.split()
            args = " ".join(args)
        elif line.startswith("when:"):
            timestamp = int(line.split("when: ")[1].strip())
            timestamps.append(timestamp)
            days_of_week[datetime.datetime.fromtimestamp(timestamp).strftime('%A')] += 1
            continue
        else: continue
    else:
        if line.startswith(":"):
            parts = line.split(';', 1)
            if len(parts) > 1 and ':' in parts[0]:
                try:
                    timestamp = int(parts[0].split(':')[1])
                    timestamps.append(timestamp)
                    days_of_week[datetime.datetime.fromtimestamp(timestamp).strftime('%A')] += 1
                except ValueError: continue
            command = parts[1] if len(parts) > 1 else ""
        else: command = line
        first_word, *args = command.split()
        args = " ".join(args)
    if not first_word: continue
    first_words.append(first_word)
    commands.append(cmd if shell == "fish" else command)
    if first_word not in args_by_cmd: args_by_cmd[first_word] = []
    if args: args_by_cmd[first_word].append(args)
times = [datetime.datetime.fromtimestamp(ts).hour for ts in timestamps]
# MAGIC BOX ENDS HERE

# first_words is a list of every binary that has been run
# timestamps is a list of every unix timestamp of every command
# times is an array with an array of hours with the hour every command is run
# args_by_cmd is a list of the arguments of every binary run after the command that ran it
# days_of_week is a list of each day of the week and how many commands have been run on that day
# Note that timestamps and times are only returned if the detected shell is ZSH or FISH


# Function to get color codes for terminal output
# Has a problem with some terminals where some colors don't show properly - idk how to fix
def getcolor(name, bold):
    colors = {"black": 30, "dark_red": 31, "green": 32, "dark_yellow": 33, "dark_blue": 34,
              "purple": 35, "teal": 36, "light_gray": 37, "dark_gray": 90, "red": 91,
              "lime": 92, "yellow": 93, "blue": 94, "magenta": 95, "cyan": 96, "white": 97}
    return f"\033[{colors.get(name, 37)}m" + ("\033[1m" if bold else "\033[22m")

# Function to set the header color from wrapped. workaround for how global variables in python work.
def setheadercolor(color):
    global headercolor
    headercolor = getcolor(color, True)

# Function to get an array of installed packages
def pkglist(commands, installed_pkgs, prefixes, name_index1, name_index2):
    pkgs = []
    for cmd in commands:
        for prefix in prefixes:
            if cmd.startswith(prefix):
                parts = cmd.split()
                pkg_name = parts[name_index1] if parts[0] == prefix.split()[0] else parts[name_index2]
                if pkg_name in installed_pkgs:
                    pkgs.append(pkg_name)
    return list(set(pkgs))

# Function to print statistics
# feed it a header, data array, item color, number color, and action
# spits out a list like 1: <item> <action> <number> times
def print_stats(title, data, color1, color2, action):
    if not data:
        return
    print(f"\n{headercolor}{title}:")
    for i, (item, count) in enumerate(data, 1):
        print(f"{getcolor('blue', False)}{i}: {getcolor(color1, False)}{item} {getcolor('blue', False)}{action} {getcolor(color2, True)}{count} {'times' if count > 1 else 'time'}")

# Function to get the package manager - works on debian and arch
# Then takes that package manager and runs the proper command to see manually installed packages
# Only arch support exists as of now so serves more of a check more than anything
def get_manager():
    with open("/etc/os-release") as f:
        data = f.read()
    if "arch" in data:
        return "pacman"
    elif "debian" in data:
       return "apt"
    else:
        return ""

# Function to display the most used arguments for a specific command
def mostargs(command, top_n, color):
    if command in args_by_cmd and args_by_cmd[command]:
        print_stats(f"Top {top_n} {command} arguments", Counter(args_by_cmd[command]).most_common(top_n), color, "green", "used")

# Function to return the top used binaries in a list by usages
def topcmds(num, color1, color2):
    print_stats(f"Top {num} used commands", Counter(first_words).most_common(num), color1, color2, "used")

# Function to clear the terminal - only works on linux shells but this program literally is for linux shells - shouldn't be a problem
def clear():
    os.system("clear")

# Print the total number of commands run
# Note that len(first_words) means total commands run
def printtotal(color):
    print(f"{headercolor}Total commands: {getcolor(color, False)}{len(first_words)}")

def percentage(command, color):
    command_count = sum(1 for cmd in commands if cmd.startswith(command + " ") or cmd == command)
    if len(first_words) > 0:
        percentage_value = (command_count / len(first_words)) * 100
        print(f"\n{headercolor}Percentage of commands that are {command}: {getcolor(color, False)}{percentage_value:.2f}%")

# Function to display the time of the first command run
# if something ever says "if timestamps" then that module only runs if the shell supports time
def firstcommand(color1, color2):
    if timestamps:
        first_command_time = datetime.datetime.fromtimestamp(timestamps[0]).strftime('%H:%M:%S on %m/%d/%y')
        print(f"\n{headercolor}First command run at {getcolor(color1, False)}{first_command_time}: {getcolor(color2, False)}{commands[0]}")
    else:
        print(f"\n{headercolor}First command: {getcolor(color2, False)}{commands[0]}")

def reset():
    print(getcolor("white", False))

# Function to display the number of commands run at each hour of the day
# Displays in a 2x12 list going from 0-12 on left and 12-23 on right
def hourly(color1, color2):
    if timestamps:
        hourly_counts = Counter(times)
        print(f"\n{headercolor}Number of commands run at each hour of the day:")
        for hour in range(12):
            left_hour, right_hour = hour, hour + 12
            left_count, right_count = hourly_counts[left_hour], hourly_counts[right_hour]

            # Space logic is to have two columns - change the 10 to a different number to change the spacing
            space = " " * (10 - len(str(left_count)))
            print(f"{getcolor(color1, False)}{left_hour:02d} - {getcolor(color2, False)}{left_count}{space}"
                f"{getcolor(color1, False)}{right_hour:02d} - {getcolor(color2, False)}{right_count}")

# Print the top pinged websites
# Different from top args in the fact that it excludes ip addresses
# You don't want those to be leaked when sharing your wrapped with others
def top_pings(top_n, color):
    if "ping" in args_by_cmd and args_by_cmd["ping"]:
        filtered_args = [arg for arg in args_by_cmd["ping"] if re.search(r'\b\d{3}\b', arg) is None and '.' in arg]
        if filtered_args:
            print_stats(f"Top {top_n} pinged IPs", Counter(filtered_args).most_common(top_n), color, "green", "used")

# This is a function to make a barchart based on incoming data. Not used by itself but by other functions.
# Currently, hourchart and daychart use this function.
def barchart(data, labels, color2, header, bar_width):
    if data:
        max_count = max(data.values()) if data else 1
        scalar = max_count / (18 if bar_width == 2 else 10)
        print(f"\n{headercolor}{header}:\n")
        for height in range(round(max_count / scalar), 0, -1):
            row = []
            for label in labels:
                count = data.get(label, 0)
                if count / scalar >= height:
                    row.append(f"{getcolor(color2, True)}{'█' * bar_width}")
                elif count / scalar >= height - 0.25:
                    row.append(f"{getcolor(color2, True)}{'▆' * bar_width}")
                elif count / scalar >= height - 0.5:
                    row.append(f"{getcolor(color2, True)}{'▄' * bar_width}")
                elif count / scalar >= height - 0.75:
                    row.append(f"{getcolor(color2, True)}{'▂' * bar_width}")
                else:
                    row.append(" " * bar_width)
            print(" ".join(row))

# This makes a barchart showing how many commands you have run at each hour of the day.
# A visual representation of the data printed by the hourly() function
def hourchart(color1, color2):
    if timestamps:
        hourly_counts = Counter(times)
        labels = range(24)
        barchart(hourly_counts, labels, color2, "Number of commands run at each hour of the day (bar chart)", 2)
        print(f"{getcolor(color1, False)}" + " ".join(f"{label:02d}" for label in labels))

def daychart(color1, color2):
    if timestamps:
        daily_counts = days_of_week
        labels = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        barchart(daily_counts, labels, color2, "Number of commands run on each day (bar chart)", 7)
        print(f"{getcolor(color1, False)}" + " ".join(f"  {label[:3]:^3}  " for label in labels))

# Function to display the number of commands run on each day of the week
# Prints out in a 1x7 list starting at saturday in format <Weekday>: <number>
def byweekday(color1, color2):
    if timestamps:
        print(f"\n{headercolor}Number of commands run by day:")
        for day, count in days_of_week.items():
            print(f"{getcolor(color1, False)}{day}: {getcolor(color2, False)}{count}")

# Function to get all packages that have been installed manually in the shell using pacman
# Takes all attempted installation commands and checks them against packages currently on the system
def pacman_pkgs(color):
    try:
        pkgs = []
        manager = get_manager()
        if manager == "pacman":
            qe_pkgs_cmd = "pacman -Qe"
        elif manager == "apt":
            qe_pkgs_cmd = "apt-mark showmanual"
        else:
            return

        qe_pkgs = subprocess.run(qe_pkgs_cmd, shell=True, capture_output=True, text=True)
        if not qe_pkgs:
            return
        qe_pkgs = set(pkg.split()[0] for pkg in qe_pkgs.stdout.splitlines())
        if manager == "pacman":
            pkgs = pkglist(args_by_cmd["sudo"], qe_pkgs, ["pacman -S "], 2, 2)
        elif manager == "apt":
            pkgs = pkglist(args_by_cmd["sudo"], qe_pkgs, ["apt install ", "apt-get install "], 2, 2)
        if pkgs:
            max_len = max(len(pkg) for pkg in pkgs)
            print(f"\n{headercolor}Packages installed using {manager}:")
            for i in range(0, len(pkgs), 2):
                pkg1 = pkgs[i]
                pkg2 = pkgs[i + 1] if i + 1 < len(pkgs) else ""
                print(f"{getcolor(color, False)}{pkg1}{' ' * (max_len - len(pkg1) + 2)}{getcolor(color, False)}{pkg2}")
    except KeyError:
        pass

# Function to get all packages that have been installed manually in the shell
# This one works for non-sudo aur helpers (paru or yay)
def aur_pkgs(man, color):
    try:
        pkgs = []
        max_len = 0
        qe_pkgs = subprocess.run(f"{man} -Qe", shell=True, capture_output=True, text=True)
        qe_pkgs = qe_pkgs.stdout.splitlines()
        for i in range(len(qe_pkgs)):
            qe_pkgs[i] = qe_pkgs[i].split()[0]
        for i in range(len(args_by_cmd[man])):
            if args_by_cmd[man][i].startswith("-S "):
                pkg = args_by_cmd[man][i].split()
                if pkg[1] in qe_pkgs:
                    if len(pkg[1]) > max_len: max_len = len(pkg[1])
                    pkgs.append(pkg[1])
        pkgs = list(set(pkgs))
        print(f"\n{headercolor}Packages installed using {man}:")
        for i in range(0, len(pkgs), 2):
            pkg1 = pkgs[i]
            pkg2 = pkgs[i + 1] if i + 1 < len(pkgs) else ""
            print(f"{getcolor(color, False)}{pkg1}{' ' * (max_len - len(pkg1) + 2)}{getcolor(color, False)}{pkg2}")
    except KeyError:
        pass

# If someone tries to run this just run wrapped.py
if __name__ == "__main__":
    os.system("python3 wrapped.py")
