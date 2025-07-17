import re
from parser import *

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

def getheadercolor():
    return headercolor

# Function to print statistics
# feed it a header, data array, item color, number color, and action
# spits out a list like 1: <item> <action> <number> times
def print_stats(title, data, color1, color2, action):
    if not data:
        return
    print(f"\n{headercolor}{title}:")
    for i, (item, count) in enumerate(data, 1):
        print(f"{getcolor('blue', False)}{i}: {getcolor(color1, False)}{item} {getcolor('blue', False)}{action} {getcolor(color2, True)}{count} {'times' if count > 1 else 'time'}")

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
        filtered_args = [arg for arg in args_by_cmd["ping"] if arg.count('.') != 3]
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
