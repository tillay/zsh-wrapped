from modules import *

setheadercolor("cyan")
clear()
printtotal("lime")
print_stats("Top 10 used commands", Counter(first_words).most_common(10), "magenta", "green", "used")
mostargs("git", 5, "yellow")
mostargs("tree", 5, "red")
mostargs("python3", 12, "green")
percentage("python3","green")
percentage("git","blue")
firstcommand("green", "magenta")
byweekday("magenta", "blue")
top_pings(5, "green")
hourly("green", "magenta")
barchart("green", "magenta")
daychart("green", "yellow")

reset()
