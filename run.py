import subprocess
import sys
import ctypes
import os
import importlib.util


def ensure_deps():
    """Ensure required Python modules are installed before importing them."""
    required = ["requests", "cryptography"]
    missing = [m for m in required if importlib.util.find_spec(m) is None]

    if missing:
        print(f"Installing missing dependencies: {', '.join(missing)}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])


def run_as_admin():
    """Relaunch the script with administrator privileges (Windows only)."""
    if os.name != "nt":
        return 

    try:
        if not ctypes.windll.shell32.IsUserAnAdmin():
            print(f"[!] Relaunching with administrator privileges...")
            script = os.path.abspath(sys.argv[0])
            params = " ".join(sys.argv[1:])
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, f'"{script}" {params}', None, 1
            )
            sys.exit(0)
    except Exception as e:
        print(f"[!] Failed to check admin privileges: {e}")


def fetch_and_exec(url: str):
    """Fetch a Python script from URL and execute it in memory."""
    try:
        import requests
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        code = compile(resp.text, url, "exec")
        exec(code, globals())
        print(f"[+] Script executed successfully. Exiting...")
        sys.exit(0)

    except Exception as e:
        print(f"[!] Failed to fetch/execute script: {e}")


def menu():
    git_repo="jesvijonathan/Ableton_Cracker"
    options = {
        "1": ("Patch", lambda: fetch_and_exec(
            f"https://raw.githubusercontent.com/{git_repo}/master/patch_ableton.py")),
        "2": ("Unpatch", lambda: fetch_and_exec(
            f"https://raw.githubusercontent.com/{git_repo}/master/undo_patch.py")),
        "3": ("Quit", lambda: sys.exit(0)),
    }

    print(f"\nAbleton Cracker [https://github.com/{git_repo}]\n")
    for key, (desc, _) in options.items():
        print(f"{key}. {desc}")

    return options


def main():
    ensure_deps()
    run_as_admin()

    options = menu()
    while True:
        choice = input("\nSelect an option: ").strip()
        action = options.get(choice)
        if action:
            action[1]()
        else:
            print(f"Invalid choice, try again.")


if __name__ == "__main__":
    main()
