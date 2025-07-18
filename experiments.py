import subprocess
import sys
import os
from modules import *

# Function to get the package manager - now works on Debian, Arch, and macOS (with Homebrew)
def get_manager():
    """
    Identifies the system's primary package manager.
    """
    if sys.platform == "darwin":  # macOS
        # Check for Homebrew on Apple Silicon or Intel paths
        if os.path.exists("/opt/homebrew/bin/brew") or os.path.exists("/usr/local/bin/brew"):
            return "brew"
    elif sys.platform.startswith("linux"):  # Linux
        try:
            with open("/etc/os-release") as f:
                data = f.read()
            if "arch" in data:
                return "pacman"
            elif "debian" in data or "ubuntu" in data:
                return "apt"
        except FileNotFoundError:
            # This case is for linux distros without /etc/os-release
            return ""
    return ""  # Return empty for unsupported OS or no manager found

# Simplified function to get an array of installed packages from command history
def pkglist(commands, installed_pkgs, prefixes, name_index):
    """
    Parses command history to find packages that were installed and are still present on the system.
    """
    pkgs = []
    for cmd in commands:
        for prefix in prefixes:
            if cmd.startswith(prefix):
                parts = cmd.split()
                if len(parts) > name_index:
                    pkg_name = parts[name_index]
                    if pkg_name in installed_pkgs:
                        pkgs.append(pkg_name)
    return list(set(pkgs))

# Function to get all packages that have been installed manually via system package manager
def system_pkgs(color):
    """
    Finds packages installed via the system's native package manager (apt, pacman, brew)
    by cross-referencing command history with currently installed packages.
    """
    try:
        manager = get_manager()
        if not manager:
            return

        # --- Get list of manually installed packages from the system ---
        if manager == "pacman":
            qe_pkgs_cmd = "pacman -Qe"
        elif manager == "apt":
            qe_pkgs_cmd = "apt-mark showmanual"
        elif manager == "brew":
            qe_pkgs_cmd = "brew leaves"
        else:
            return

        qe_pkgs_result = subprocess.run(qe_pkgs_cmd, shell=True, capture_output=True, text=True, check=False)
        if qe_pkgs_result.returncode != 0:
            return

        if manager in ["pacman", "apt"]:
            installed_pkgs = set(pkg.split()[0] for pkg in qe_pkgs_result.stdout.splitlines())
        else:  # brew
            installed_pkgs = set(qe_pkgs_result.stdout.splitlines())

        # --- Check history for installation commands ---
        pkgs = []
        if manager == "pacman":
            if "sudo" in args_by_cmd:
                pkgs = pkglist(args_by_cmd["sudo"], installed_pkgs, ["pacman -S "], 2)
        elif manager == "apt":
            if "sudo" in args_by_cmd:
                pkgs = pkglist(args_by_cmd["sudo"], installed_pkgs, ["apt install ", "apt-get install "], 2)
        elif manager == "brew":
            if "brew" in args_by_cmd:
                pkgs = pkglist(args_by_cmd["brew"], installed_pkgs, ["install "], 1)

        if pkgs:
            max_len = max(len(pkg) for pkg in pkgs) if pkgs else 0
            print(f"\n{getheadercolor()}Packages installed using {manager}:")
            for i in range(0, len(pkgs), 2):
                pkg1 = pkgs[i]
                pkg2 = pkgs[i + 1] if i + 1 < len(pkgs) else ""
                print(f"{getcolor(color, False)}{pkg1}{' ' * (max_len - len(pkg1) + 2)}{getcolor(color, False)}{pkg2}")

    except (KeyError, FileNotFoundError):
        # Gracefully fail if a command isn't in history or another file issue occurs.
        pass

# Function to get all packages that have been installed manually in the shell
# This one works for non-sudo aur helpers (paru or yay)
def aur_pkgs(man, color):
    """
    Finds packages installed using an AUR helper (Arch Linux specific).
    """
    # This function is specific to Arch Linux AUR helpers, so we check the manager.
    if get_manager() != "pacman":
        return
    try:
        pkgs = []
        max_len = 0
        qe_pkgs_result = subprocess.run(f"{man} -Qe", shell=True, capture_output=True, text=True, check=False)
        if qe_pkgs_result.returncode != 0:
            return
            
        qe_pkgs = {pkg.split()[0] for pkg in qe_pkgs_result.stdout.splitlines()}
        
        if man in args_by_cmd:
            for cmd in args_by_cmd[man]:
                if cmd.startswith("-S "):
                    pkg_name = cmd.split()[1]
                    if pkg_name in qe_pkgs:
                        if len(pkg_name) > max_len: max_len = len(pkg_name)
                        pkgs.append(pkg_name)

        pkgs = list(set(pkgs))
        if pkgs:
            print(f"\n{getheadercolor()}Packages installed using {man}:")
            for i in range(0, len(pkgs), 2):
                pkg1 = pkgs[i]
                pkg2 = pkgs[i + 1] if i + 1 < len(pkgs) else ""
                print(f"{getcolor(color, False)}{pkg1}{' ' * (max_len - len(pkg1) + 2)}{getcolor(color, False)}{pkg2}")
    except (KeyError, FileNotFoundError):
        pass
