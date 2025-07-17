import subprocess
from modules import *

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
            print(f"\n{getheadercolor()}Packages installed using {manager}:")
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
        print(f"\n{getheadercolor()}Packages installed using {man}:")
        for i in range(0, len(pkgs), 2):
            pkg1 = pkgs[i]
            pkg2 = pkgs[i + 1] if i + 1 < len(pkgs) else ""
            print(f"{getcolor(color, False)}{pkg1}{' ' * (max_len - len(pkg1) + 2)}{getcolor(color, False)}{pkg2}")
    except KeyError:
        pass

