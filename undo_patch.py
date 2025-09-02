import json
import re
import os
import platform
from ctypes import windll
from subprocess import list2cmdline
import sys

def read_config_from_json(json_file_path="config.json"):
    """Reads configuration from the specified JSON file and swaps signkeys."""
    try:
        if not os.path.exists("./file_path"):
            print(f"Config file {json_file_path} not found. Downloading...")
            url = "https://raw.githubusercontent.com/jesvijonathan/Ableton_Cracker/master/config.json"
            os.system(f'curl -o "{json_file_path}" "{url}"')

        with open(json_file_path, 'r') as json_file:
            data = json.load(json_file)

        file_path = data.get("file_path")
        old_signkey = data.get("new_signkey")
        new_signkey = data.get("old_signkey")

        if not all([file_path, old_signkey, new_signkey]):
            raise ValueError("JSON must include 'file_path', 'old_signkey', and 'new_signkey'.")

        return file_path, old_signkey, new_signkey

    except (FileNotFoundError, json.JSONDecodeError) as e:
        raise RuntimeError(f"Config error: {e}")

def find_installations():
    """Detects Ableton Live installations across OS."""
    system = platform.system()
    installations = []

    if system == "Windows":
        base_dir = r"C:\ProgramData\Ableton"
        if os.path.isdir(base_dir):
            for entry in os.listdir(base_dir):
                program_dir = os.path.join(base_dir, entry, "Program")
                if os.path.isdir(program_dir):
                    for file in os.listdir(program_dir):
                        if file.endswith(".exe") and "Live" in file:
                            installations.append((os.path.join(program_dir, file), entry))

    elif system == "Linux":
        wine_base = os.path.expanduser("~/.wine/drive_c/ProgramData/Ableton")
        if os.path.isdir(wine_base):
            for entry in os.listdir(wine_base):
                program_dir = os.path.join(wine_base, entry, "Program")
                if os.path.isdir(program_dir):
                    for file in os.listdir(program_dir):
                        if file.endswith(".exe") and "Live" in file:
                            installations.append((os.path.join(program_dir, file), entry))

    elif system == "Darwin":
        base_dir = "/Applications"
        if os.path.isdir(base_dir):
            for entry in os.listdir(base_dir):
                if entry.endswith(".app") and "Ableton Live" in entry:
                    exe_path = os.path.join(base_dir, entry, "Contents", "MacOS", "Live")
                    if os.path.exists(exe_path):
                        installations.append((exe_path, entry.replace(".app", "")))
                        
    return installations

def replace_signkey_in_file(file_path, old_signkey, new_signkey):
    """Replaces a hexadecimal signkey within a binary file."""

    old_signkey, new_signkey = (s[2:] if s.startswith("0x") else s for s in (old_signkey, new_signkey))

    if len(old_signkey) != len(new_signkey):
        raise ValueError("Signkeys must have equal length.")
    if not all(re.fullmatch(r'[0-9a-fA-F]+', s) for s in (old_signkey, new_signkey)):
        raise ValueError("Invalid hex string(s).")

    old_bytes, new_bytes = bytes.fromhex(old_signkey), bytes.fromhex(new_signkey)

    try:
        with open(file_path, 'rb+') as f:
            content = f.read()
            if old_bytes not in content:
                msg = "Already unpatched." if new_bytes in content else "Patched signkey not found."
                print(msg)
                return

            f.seek(0)
            f.write(content.replace(old_bytes, new_bytes))
            f.truncate()
            print(f"Signkey successfully reverted.")

    except FileNotFoundError:
        raise RuntimeError(f"File not found: {file_path}")
    except PermissionError:
        raise RuntimeError("Permission denied. Try running as Administrator or with sudo.")

def choose_installation(installations, config_path=None):
    """Let the user pick a detected installation, config.json path, or quit."""
    print(f"\nFound Ableton installations:")
    for i, (path, name) in enumerate(installations, start=1):
        print(f"{i}. {name} at {path}")

    option_count = len(installations)

    if config_path and config_path.lower() != "auto":
        option_count += 1
        print(f"{option_count}. Use config.json path → {config_path}")

    print(f"{option_count+1}. Quit")

    try:
        choice = int(input("\nSelect installation: "))

        if 1 <= choice <= len(installations):
            return installations[choice-1][0]
        elif config_path and config_path.lower() != "auto" and choice == option_count:
            return config_path
        elif choice == option_count+1:
            print(f"Exiting without changes.")
            return None
        else:
            print(f"Invalid choice. Defaulting to first installation.")
            return installations[0][0]
    except ValueError:
        print(f"Invalid input. Defaulting to first installation.")
        return installations[0][0]

def is_admin():
    """Check if the script is running with administrator privileges"""
    try:
        return windll.shell32.IsUserAnAdmin() != 0
    except:
        return False
    
def run_as_admin():
    """Relaunch the script with administrator privileges"""
    script = os.path.abspath(sys.argv[0])
    params = list2cmdline(sys.argv[1:])
    windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)
    sys.exit(0)

def main():
    # Request admin on Windows if needed
    if platform.system() == "Windows" and not is_admin():
        print("\nThis operation requires administrator privileges on Windows.")
        print("Relaunching with admin rights...")
        run_as_admin()
        return
    
    try:
        file_path, old_signkey, new_signkey = read_config_from_json()

        if file_path.lower() == "auto":
            installations = find_installations()
            if not installations:
                raise RuntimeError("No Ableton Live installations found. Update config.json manually.")
            file_path = choose_installation(installations, None)
            if not file_path:
                return

        replace_signkey_in_file(file_path, old_signkey, new_signkey)
        print(f"\nUnpatch completed successfully!")

    except Exception as e:
        print(f"\nUnpatch failed: {e}")

    input("Press Enter to exit...")
    sys.exit(1)

if __name__ == "__main__":
    main()
